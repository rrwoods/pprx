from datetime import timedelta
import json
import math
from unittest.mock import Mock, patch
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.utils import timezone
from scorebrowser.misc import sort_key
from scorebrowser.models import Chart, ChartUnlock, Difficulty, Song, UnlockTask, User, UserScore, Version
from scorebrowser.synchronization import (
    ReauthRequired,
    SanbaiScoreSource,
    SynchronizationOutcome,
    SynchronizationResult,
    UpstreamError,
    UpstreamScore,
    UpstreamScoreSource,
    is_synchronization_in_progress,
    synchronize,
)
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.fakes import FakeScoreSource
from scorebrowser.tests.helpers import create_chart, create_song, create_user


class SynchronizationTests(PPRXTestCase):
    def test_synchronize_empty_scores_returns_synchronized(self):
        user = create_user()
        fake = FakeScoreSource(scores=[])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 0)
        self.assertEqual(result.superseded_scores, 0)
        self.assertEqual(result.corrected_fields, 0)

    def test_synchronize_reauth_required_sets_user_reauth_and_returns_outcome(self):
        user = create_user(reauth=False)
        fake = FakeScoreSource(reauth_required=True)

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.REAUTH_REQUIRED)
        user.refresh_from_db()
        self.assertTrue(user.reauth)

    def test_synchronize_upstream_error_returns_outcome_with_status_and_body(self):
        user = create_user()
        fake = FakeScoreSource(upstream_error=(502, "Bad Gateway from 3icecream"))

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.UPSTREAM_ERROR)
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.error_body, "Bad Gateway from 3icecream")

    def test_first_time_score_ingestion(self):
        user = create_user()
        song = create_song(id="song_1", title="Test Song")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=12)

        upstream_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=12,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000000,
            flare_gauge=7,
        )
        fake = FakeScoreSource(scores=[upstream_score])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)
        self.assertEqual(result.superseded_scores, 0)
        self.assertEqual(result.corrected_fields, 0)

        user_scores = UserScore.objects.filter(user=user, chart=chart)
        self.assertEqual(user_scores.count(), 1)
        score_record = user_scores.first()
        self.assertTrue(score_record.current)
        self.assertEqual(score_record.score, 950000)
        self.assertEqual(score_record.clear_type, 3)
        self.assertEqual(score_record.flare_gauge, 7)
        self.assertEqual(score_record.timestamp, 1700000000)

    def test_normalized_score_calculation_including_mfc_ceiling(self):
        user = create_user()
        song = create_song(id="song_norm", title="Norm Song")
        chart_normal = create_chart(song=song, difficulty=Difficulty.objects.get(id=1), rating=8)
        chart_mfc = create_chart(song=song, difficulty=Difficulty.objects.get(id=2), rating=10)

        scores = [
            UpstreamScore(
                song_id=song.id,
                difficulty=1,
                rating=8,
                song_title=song.title,
                score=990000,
                lamp=4,
                timestamp=1700000001,
            ),
            UpstreamScore(
                song_id=song.id,
                difficulty=2,
                rating=10,
                song_title=song.title,
                score=1000000,
                lamp=5,
                timestamp=1700000002,
            ),
        ]
        fake = FakeScoreSource(scores=scores)

        result = synchronize(user, fake)
        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)

        record_normal = UserScore.objects.get(user=user, chart=chart_normal)
        expected_normalized = -math.log2(1000000 - 990000)
        self.assertAlmostEqual(record_normal.normalized, expected_normalized, places=6)

        record_mfc = UserScore.objects.get(user=user, chart=chart_mfc)
        self.assertEqual(record_mfc.normalized, -2.323)

    def test_quality_evaluated_only_for_cleared_scores_with_valid_breakpoints(self):
        user = create_user()
        song = create_song(id="song_qual", title="Quality Song")
        norm_bps = [-14.0, -10.0]
        qual_bps = [10.0, 15.0]
        chart_with_bps = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=1),
            rating=10,
            normscore_breakpoints=json.dumps(norm_bps),
            quality_breakpoints=json.dumps(qual_bps),
        )
        chart_without_bps = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=2),
            rating=10,
            normscore_breakpoints="",
            quality_breakpoints="",
        )

        scores = [
            # Cleared with breakpoints -> quality evaluated
            UpstreamScore(
                song_id=song.id,
                difficulty=1,
                rating=10,
                song_title=song.title,
                score=990000,
                lamp=1,
                timestamp=1700000010,
            ),
            # Cleared without breakpoints -> quality is None
            UpstreamScore(
                song_id=song.id,
                difficulty=2,
                rating=10,
                song_title=song.title,
                score=990000,
                lamp=1,
                timestamp=1700000011,
            ),
        ]
        fake = FakeScoreSource(scores=scores)
        synchronize(user, fake)

        rec_with_bps = UserScore.objects.get(user=user, chart=chart_with_bps)
        self.assertIsNotNone(rec_with_bps.quality)
        expected_qual = float(math.fsum([
            qual_bps[0],
            (rec_with_bps.normalized - norm_bps[0]) / (norm_bps[1] - norm_bps[0]) * (qual_bps[1] - qual_bps[0])
        ]))
        self.assertAlmostEqual(rec_with_bps.quality, expected_qual, places=4)

        rec_without_bps = UserScore.objects.get(user=user, chart=chart_without_bps)
        self.assertIsNone(rec_without_bps.quality)

        # Now test failed score (lamp=0) with valid breakpoints -> quality must be None
        user2 = create_user()
        failed_score = [
            UpstreamScore(
                song_id=song.id,
                difficulty=1,
                rating=10,
                song_title=song.title,
                score=950000,
                lamp=0,
                timestamp=1700000012,
            ),
        ]
        synchronize(user2, FakeScoreSource(scores=failed_score))
        rec_failed = UserScore.objects.get(user=user2, chart=chart_with_bps)
        self.assertIsNone(rec_failed.quality)

    def test_doubles_charts_skipped(self):
        user = create_user()
        song = create_song(id="song_dp", title="Doubles Song")
        # difficulty 5 is Basic DP
        scores = [
            UpstreamScore(
                song_id=song.id,
                difficulty=5,
                rating=10,
                song_title=song.title,
                score=990000,
                lamp=3,
                timestamp=1700000020,
            ),
        ]
        fake = FakeScoreSource(scores=scores)
        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 0)
        self.assertEqual(UserScore.objects.filter(user=user).count(), 0)

    def test_improved_score_supersedes_old_current_score(self):
        user = create_user()
        song = create_song(id="song_imp_score")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=900000,
            lamp=3,
            timestamp=1700000030,
            flare_gauge=5,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))
        old_record = UserScore.objects.get(user=user, chart=chart, current=True)

        second_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=920000,
            lamp=3,
            timestamp=1700000040,
            flare_gauge=5,
        )
        result = synchronize(user, FakeScoreSource(scores=[second_score]))

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 0)
        self.assertEqual(result.superseded_scores, 1)
        self.assertEqual(result.corrected_fields, 0)

        old_record.refresh_from_db()
        self.assertIsNone(old_record.current)

        new_record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(new_record.score, 920000)
        self.assertEqual(new_record.clear_type, 3)
        self.assertEqual(new_record.flare_gauge, 5)
        self.assertEqual(new_record.timestamp, 1700000040)
        self.assertEqual(UserScore.objects.filter(user=user, chart=chart, current=True).count(), 1)
        self.assertEqual(UserScore.objects.filter(user=user, chart=chart).count(), 2)

    def test_improved_lamp_supersedes_old_current_score(self):
        user = create_user()
        song = create_song(id="song_imp_lamp")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=2,
            timestamp=1700000050,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))

        second_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000060,
        )
        result = synchronize(user, FakeScoreSource(scores=[second_score]))

        self.assertEqual(result.superseded_scores, 1)
        new_record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(new_record.clear_type, 3)

    def test_improved_flare_gauge_supersedes_old_current_score(self):
        user = create_user()
        song = create_song(id="song_imp_flare")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000070,
            flare_gauge=4,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))

        second_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000080,
            flare_gauge=6,
        )
        result = synchronize(user, FakeScoreSource(scores=[second_score]))

        self.assertEqual(result.superseded_scores, 1)
        new_record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(new_record.flare_gauge, 6)

    def test_field_merge_never_regresses_lamp_when_score_improves(self):
        user = create_user()
        song = create_song(id="song_merge_lamp")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        # Stored: 900,000 with PFC (lamp 4)
        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=900000,
            lamp=4,
            timestamp=1700000090,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))

        # Upstream has higher score (950,000) but lower lamp (2)
        second_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=2,
            timestamp=1700000100,
        )
        result = synchronize(user, FakeScoreSource(scores=[second_score]))

        self.assertEqual(result.superseded_scores, 1)
        self.assertEqual(result.corrected_fields, 1)

        new_record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(new_record.score, 950000)
        self.assertEqual(new_record.clear_type, 4)  # PFC preserved!

    def test_missing_upstream_flare_does_not_overwrite_stored_flare(self):
        user = create_user()
        song = create_song(id="song_flare_missing")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        # Stored: flare 7
        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=900000,
            lamp=3,
            timestamp=1700000110,
            flare_gauge=7,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))

        # Upstream has higher score (920,000), same lamp, but missing flare (None)
        second_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=920000,
            lamp=3,
            timestamp=1700000120,
            flare_gauge=None,
        )
        result = synchronize(user, FakeScoreSource(scores=[second_score]))

        self.assertEqual(result.superseded_scores, 1)
        self.assertEqual(result.corrected_fields, 1)

        new_record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(new_record.score, 920000)
        self.assertEqual(new_record.flare_gauge, 7)  # Flare gauge 7 preserved!

    def test_ties_and_lower_upstream_records_do_not_supersede(self):
        user = create_user()
        song = create_song(id="song_tie")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        first_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000130,
            flare_gauge=5,
        )
        synchronize(user, FakeScoreSource(scores=[first_score]))
        original_record = UserScore.objects.get(user=user, chart=chart, current=True)

        # 1. Exact tie
        tie_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=950000,
            lamp=3,
            timestamp=1700000140,
            flare_gauge=5,
        )
        result_tie = synchronize(user, FakeScoreSource(scores=[tie_score]))
        self.assertEqual(result_tie.superseded_scores, 0)
        self.assertEqual(result_tie.new_scores, 0)
        self.assertEqual(result_tie.corrected_fields, 0)
        self.assertEqual(UserScore.objects.filter(user=user, chart=chart).count(), 1)

        # 2. Lower upstream values in all fields
        lower_score = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=900000,
            lamp=2,
            timestamp=1700000150,
            flare_gauge=3,
        )
        result_lower = synchronize(user, FakeScoreSource(scores=[lower_score]))
        self.assertEqual(result_lower.superseded_scores, 0)
        self.assertEqual(result_lower.new_scores, 0)
        self.assertEqual(result_lower.corrected_fields, 3)

        original_record.refresh_from_db()
        self.assertTrue(original_record.current)
        self.assertEqual(original_record.score, 950000)
        self.assertEqual(original_record.clear_type, 3)
        self.assertEqual(original_record.flare_gauge, 5)
        self.assertEqual(UserScore.objects.filter(user=user, chart=chart).count(), 1)

    def test_unknown_song_and_chart_discovery_creates_version_20_song_and_hidden_chart(self):
        user = create_user()
        upstream = UpstreamScore(
            song_id="brand_new_song",
            difficulty=3,
            rating=14,
            song_title="Brand New Song",
            score=960000,
            lamp=3,
            timestamp=1700000200,
        )
        fake = FakeScoreSource(scores=[upstream])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)

        # Song was created with version 20 and sort_key
        song = Song.objects.get(id="brand_new_song")
        self.assertEqual(song.version_id, 20)
        self.assertEqual(song.title, "Brand New Song")
        self.assertEqual(song.sort_key, sort_key("Brand New Song"))

        # Hidden Chart was created with rating 14
        chart = Chart.objects.get(song=song, difficulty_id=3)
        self.assertEqual(chart.rating, 14)
        self.assertTrue(chart.hidden)

        # Version 20 chart does not create A3+ unlock task link
        self.assertFalse(ChartUnlock.objects.filter(chart=chart).exists())

    def test_unknown_chart_discovery_on_pre_a3_song_creates_a3_plus_unlock_link(self):
        user = create_user()
        v18 = Version.objects.get(id=18)
        song = create_song(id="pre_a3_song", version=v18, title="Old Song")

        upstream = UpstreamScore(
            song_id=song.id,
            difficulty=4,  # Challenge
            rating=16,
            song_title=song.title,
            score=930000,
            lamp=2,
            timestamp=1700000210,
        )
        fake = FakeScoreSource(scores=[upstream])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)

        chart = Chart.objects.get(song=song, difficulty_id=4)
        self.assertTrue(chart.hidden)
        self.assertEqual(chart.rating, 16)

        challenge_task = UnlockTask.objects.get(name="New Challenge charts (A3+)")
        unlock_link = ChartUnlock.objects.filter(chart=chart, task=challenge_task)
        self.assertTrue(unlock_link.exists())

    def test_unknown_non_challenge_chart_discovery_on_pre_a3_song_does_not_create_unlock_link(self):
        user = create_user()
        v18 = Version.objects.get(id=18)
        song = create_song(id="pre_a3_song_basic", version=v18, title="Old Song Basic")

        upstream = UpstreamScore(
            song_id=song.id,
            difficulty=1,  # Basic
            rating=5,
            song_title=song.title,
            score=980000,
            lamp=4,
            timestamp=1700000215,
        )
        fake = FakeScoreSource(scores=[upstream])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        chart = Chart.objects.get(song=song, difficulty_id=1)
        self.assertFalse(ChartUnlock.objects.filter(chart=chart).exists())

    def test_duplicate_upstream_scores_for_same_chart_are_merged(self):
        user = create_user()
        song = create_song(id="song_dup")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)

        # Two records for the same chart: one with higher score, one with better lamp & flare
        upstream1 = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=980000,
            lamp=2,
            timestamp=1700000230,
            flare_gauge=None,
        )
        upstream2 = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=15,
            song_title=song.title,
            score=920000,
            lamp=4,
            timestamp=1700000240,
            flare_gauge=8,
        )
        fake = FakeScoreSource(scores=[upstream1, upstream2])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)

        record = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(record.score, 980000)
        self.assertEqual(record.clear_type, 4)
        self.assertEqual(record.flare_gauge, 8)
        self.assertEqual(record.timestamp, 1700000240)


    def test_unknown_chart_discovery_on_post_a3_song_does_not_create_unlock_link(self):
        user = create_user()
        v19 = Version.objects.get(id=19)
        song = create_song(id="post_a3_song", version=v19, title="A3 Song")

        upstream = UpstreamScore(
            song_id=song.id,
            difficulty=4,
            rating=17,
            song_title=song.title,
            score=910000,
            lamp=1,
            timestamp=1700000220,
        )
        fake = FakeScoreSource(scores=[upstream])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        chart = Chart.objects.get(song=song, difficulty_id=4)
        self.assertFalse(ChartUnlock.objects.filter(chart=chart).exists())

    def test_is_synchronization_in_progress_reflects_claim_freshness(self):
        idle_user = create_user(synchronization_started_at=None)
        fresh_user = create_user(synchronization_started_at=timezone.now() - timedelta(minutes=5))
        stale_user = create_user(synchronization_started_at=timezone.now() - timedelta(minutes=10, seconds=1))

        self.assertFalse(is_synchronization_in_progress(idle_user))
        self.assertTrue(is_synchronization_in_progress(fresh_user))
        self.assertFalse(is_synchronization_in_progress(stale_user))

    def test_synchronize_acquires_claim_before_fetch_and_rejects_concurrent_run(self):
        user = create_user()
        inner_fake = FakeScoreSource(scores=[])
        observations = {}

        def check_during_fetch(fetching_user):
            db_user = User.objects.get(id=fetching_user.id)
            observations['started_at'] = db_user.synchronization_started_at
            observations['in_progress'] = is_synchronization_in_progress(db_user)
            observations['concurrent_result'] = synchronize(db_user, inner_fake)

        outer_fake = FakeScoreSource(scores=[], on_fetch=check_during_fetch)

        result = synchronize(user, outer_fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertIsNotNone(observations['started_at'])
        self.assertTrue(observations['in_progress'])
        self.assertEqual(observations['concurrent_result'].outcome, SynchronizationOutcome.ALREADY_RUNNING)
        self.assertEqual(inner_fake.calls, 0)

    def test_synchronize_rejects_preexisting_fresh_claim_without_calling_source(self):
        started_at = timezone.now() - timedelta(minutes=5)
        user = create_user(synchronization_started_at=started_at)
        fake = FakeScoreSource(scores=[])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.ALREADY_RUNNING)
        self.assertEqual(fake.calls, 0)
        user.refresh_from_db()
        self.assertEqual(user.synchronization_started_at, started_at)

    def test_synchronize_releases_claim_after_success(self):
        user = create_user()
        fake = FakeScoreSource(scores=[])

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertFalse(is_synchronization_in_progress(user))
        user.refresh_from_db()
        self.assertIsNone(user.synchronization_started_at)

    def test_synchronize_releases_claim_after_reauth_required(self):
        user = create_user()
        fake = FakeScoreSource(reauth_required=True)

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.REAUTH_REQUIRED)
        user.refresh_from_db()
        self.assertIsNone(user.synchronization_started_at)

    def test_synchronize_releases_claim_after_upstream_error(self):
        user = create_user()
        fake = FakeScoreSource(upstream_error=(503, "Service Unavailable"))

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.UPSTREAM_ERROR)
        user.refresh_from_db()
        self.assertIsNone(user.synchronization_started_at)

    def test_synchronize_releases_claim_when_exception_propagates(self):
        user = create_user()

        def fail_unexpectedly(_fetching_user):
            raise RuntimeError("boom")

        fake = FakeScoreSource(on_fetch=fail_unexpectedly)

        with self.assertRaises(RuntimeError):
            synchronize(user, fake)

        self.assertFalse(is_synchronization_in_progress(user))
        user.refresh_from_db()
        self.assertIsNone(user.synchronization_started_at)

    def test_synchronize_reclaims_stale_claim_older_than_10_minutes(self):
        stale_started_at = timezone.now() - timedelta(minutes=10, seconds=1)
        user = create_user(synchronization_started_at=stale_started_at)
        song = create_song(id="song_stale")
        create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=12)
        observations = {}

        def observe_claim(fetching_user):
            db_user = User.objects.get(id=fetching_user.id)
            observations['during_started_at'] = db_user.synchronization_started_at
            observations['during_in_progress'] = is_synchronization_in_progress(db_user)

        upstream = UpstreamScore(
            song_id=song.id,
            difficulty=3,
            rating=12,
            song_title=song.title,
            score=940000,
            lamp=3,
            timestamp=1700000300,
        )
        fake = FakeScoreSource(scores=[upstream], on_fetch=observe_claim)

        self.assertFalse(is_synchronization_in_progress(user))
        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)
        self.assertGreater(observations['during_started_at'], stale_started_at)
        self.assertTrue(observations['during_in_progress'])
        user.refresh_from_db()
        self.assertIsNone(user.synchronization_started_at)

    def test_synchronize_does_not_release_newer_claim_after_takeover(self):
        user = create_user()
        newer_claim = timezone.now() + timedelta(minutes=11)

        def simulate_takeover(fetching_user):
            User.objects.filter(id=fetching_user.id).update(synchronization_started_at=newer_claim)

        fake = FakeScoreSource(scores=[], on_fetch=simulate_takeover)

        result = synchronize(user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        user.refresh_from_db()
        self.assertEqual(user.synchronization_started_at, newer_claim)

    def test_fresh_claim_on_one_user_does_not_block_other_user(self):
        create_user(synchronization_started_at=timezone.now() - timedelta(minutes=2))
        other_user = create_user()
        fake = FakeScoreSource(scores=[])

        result = synchronize(other_user, fake)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)


def _mock_response(status_code=200, json_data=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    if json_data is not None:
        response.json.return_value = json_data
    else:
        response.json.side_effect = ValueError("No JSON")
    return response


class SanbaiScoreSourceTests(PPRXTestCase):
    def test_fetch_scores_success_translates_payload(self):
        user = create_user(access_token="tok_123", refresh_token="ref_123")
        payload = [
            {
                "song_id": "song_a",
                "difficulty": 3,
                "rating": 14,
                "song_name": "Song A",
                "score": 985000,
                "lamp": 4,
                "flare": 8,
                "time_played": 1700000100,
                "time_uploaded": 1700000200,
            },
            {
                "song_id": "song_b",
                "difficulty": 6,
                "rating": 15,
                "song_name": "Song B Doubles",
                "score": 910000,
                "lamp": 2,
                "time_played": 0,
                "time_uploaded": 1700000300,
            },
        ]
        source = SanbaiScoreSource()

        with patch("scorebrowser.synchronization.requests.post", return_value=_mock_response(200, payload)) as mock_post:
            scores = source.fetch_scores(user)

        mock_post.assert_called_once_with(
            "https://3icecream.com/dev/api/v1/get_scores",
            data={"access_token": "tok_123"},
        )
        self.assertEqual(
            scores,
            [
                UpstreamScore(
                    song_id="song_a",
                    difficulty=3,
                    rating=14,
                    song_title="Song A",
                    score=985000,
                    lamp=4,
                    timestamp=1700000100,
                    flare_gauge=8,
                ),
                UpstreamScore(
                    song_id="song_b",
                    difficulty=6,
                    rating=15,
                    song_title="Song B Doubles",
                    score=910000,
                    lamp=2,
                    timestamp=1700000300,
                    flare_gauge=None,
                ),
            ],
        )

    def test_fetch_scores_400_refreshes_tokens_and_retries_once(self):
        user = create_user(access_token="old_access", refresh_token="old_refresh")
        payload = [
            {
                "song_id": "song_retry",
                "difficulty": 4,
                "rating": 17,
                "song_name": "Retry Song",
                "score": 995000,
                "lamp": 5,
                "flare": 10,
                "time_played": 1700000500,
                "time_uploaded": 1700000500,
            }
        ]
        responses = [
            _mock_response(400, text="expired token"),
            _mock_response(200, {"access_token": "new_access", "refresh_token": "new_refresh"}),
            _mock_response(200, payload),
        ]
        source = SanbaiScoreSource()

        with patch("scorebrowser.synchronization.requests.post", side_effect=responses) as mock_post:
            scores = source.fetch_scores(user)

        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(
            mock_post.call_args_list[0].args,
            ("https://3icecream.com/dev/api/v1/get_scores",),
        )
        self.assertEqual(
            mock_post.call_args_list[0].kwargs,
            {"data": {"access_token": "old_access"}},
        )
        self.assertEqual(
            mock_post.call_args_list[1].args,
            ("https://3icecream.com/oauth/token",),
        )
        self.assertEqual(
            mock_post.call_args_list[1].kwargs,
            {
                "data": {
                    "client_id": settings.CLIENT_ID,
                    "client_secret": settings.CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": "old_refresh",
                    "redirect_uri": settings.SANBAI_OAUTH_REDIRECT_URI,
                }
            },
        )
        self.assertEqual(
            mock_post.call_args_list[2].args,
            ("https://3icecream.com/dev/api/v1/get_scores",),
        )
        self.assertEqual(
            mock_post.call_args_list[2].kwargs,
            {"data": {"access_token": "new_access"}},
        )

        user.refresh_from_db()
        self.assertEqual(user.access_token, "new_access")
        self.assertEqual(user.refresh_token, "new_refresh")
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0].song_id, "song_retry")

    def test_fetch_scores_failed_refresh_raises_reauth_required_and_sets_reauth(self):
        user = create_user(access_token="old_access", refresh_token="bad_refresh", reauth=False)
        responses = [
            _mock_response(400, text="expired token"),
            _mock_response(400, {"error": "invalid_grant"}, text='{"error": "invalid_grant"}'),
        ]
        source = SanbaiScoreSource()

        with patch("scorebrowser.synchronization.requests.post", side_effect=responses) as mock_post:
            with self.assertRaises(ReauthRequired):
                source.fetch_scores(user)

        self.assertEqual(mock_post.call_count, 2)
        user.refresh_from_db()
        self.assertTrue(user.reauth)

    def test_fetch_scores_malformed_refresh_payload_raises_reauth_required(self):
        user = create_user(access_token="old_access", refresh_token="bad_refresh", reauth=False)
        responses = [
            _mock_response(400, text="expired token"),
            _mock_response(200, {"error": "missing_tokens"}, text='{"error": "missing_tokens"}'),
        ]
        source = SanbaiScoreSource()

        with patch("scorebrowser.synchronization.requests.post", side_effect=responses) as mock_post:
            with self.assertRaises(ReauthRequired):
                source.fetch_scores(user)

        self.assertEqual(mock_post.call_count, 2)
        user.refresh_from_db()
        self.assertTrue(user.reauth)

    def test_fetch_scores_non_200_raises_upstream_error_without_refresh(self):
        user = create_user(access_token="tok_123", refresh_token="ref_123")
        source = SanbaiScoreSource()

        with patch(
            "scorebrowser.synchronization.requests.post",
            return_value=_mock_response(502, text="Bad Gateway"),
        ) as mock_post:
            with self.assertRaises(UpstreamError) as ctx:
                source.fetch_scores(user)

        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(ctx.exception.status, 502)
        self.assertEqual(ctx.exception.body, "Bad Gateway")

    def test_fetch_scores_400_after_retry_raises_upstream_error_without_second_refresh(self):
        user = create_user(access_token="old_access", refresh_token="old_refresh")
        responses = [
            _mock_response(400, text="expired token"),
            _mock_response(200, {"access_token": "new_access", "refresh_token": "new_refresh"}),
            _mock_response(400, text="still bad request"),
        ]
        source = SanbaiScoreSource()

        with patch("scorebrowser.synchronization.requests.post", side_effect=responses) as mock_post:
            with self.assertRaises(UpstreamError) as ctx:
                source.fetch_scores(user)

        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.body, "still bad request")
        user.refresh_from_db()
        self.assertFalse(user.reauth)

    def test_synchronize_defaults_to_sanbai_score_source(self):
        user = create_user(access_token="tok_default", refresh_token="ref_default")
        song = create_song(id="song_default", title="Default Adapter Song")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=12)
        payload = [
            {
                "song_id": song.id,
                "difficulty": 3,
                "rating": 12,
                "song_name": song.title,
                "score": 960000,
                "lamp": 3,
                "flare": 6,
                "time_played": 1700000600,
                "time_uploaded": 1700000600,
            }
        ]

        with patch("scorebrowser.synchronization.requests.post", return_value=_mock_response(200, payload)):
            result = synchronize(user)

        self.assertEqual(result.outcome, SynchronizationOutcome.SYNCHRONIZED)
        self.assertEqual(result.new_scores, 1)
        stored = UserScore.objects.get(user=user, chart=chart, current=True)
        self.assertEqual(stored.score, 960000)
        self.assertEqual(stored.flare_gauge, 6)


class MaintainerMailTests(PPRXTestCase):
    def test_testmail_sends_to_maintainer_email_setting(self):
        self.assertEqual(settings.MAINTAINER_EMAIL, "rick.r.woods@gmail.com")
        with self.settings(MAINTAINER_EMAIL="override-maintainer@example.com"):
            call_command("testmail")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["override-maintainer@example.com"])



