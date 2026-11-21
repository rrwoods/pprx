import importlib
from io import StringIO
import json
from unittest.mock import patch

from django.apps import apps
from django.core import mail

from scorebrowser.models import Difficulty, UserScore
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.helpers import create_chart, create_song, create_user, create_user_score


MIGRATION_MODULE = "scorebrowser.migrations.0206_repair_current_scores"


class RepairMigrationTests(PPRXTestCase):
    def _run_forward(self):
        migration = importlib.import_module(MIGRATION_MODULE)
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            migration.forward(apps, None)
        return stdout.getvalue()

    def test_zero_affected_rows_sends_email_and_logs_report(self):
        user = create_user(player_id="p_clean", with_django_user=True)
        song = create_song(id="song_clean", title="Clean Song")
        chart = create_chart(song=song)
        create_user_score(user=user, chart=chart, score=950000, clear_type=3, flare_gauge=5, current=True)
        create_user_score(user=user, chart=chart, score=900000, clear_type=2, flare_gauge=3, current=None)

        with self.settings(MAINTAINER_EMAIL="maintainer@example.com"):
            output = self._run_forward()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["maintainer@example.com"])
        self.assertIn("0", email.body)
        self.assertIn("affected", email.body.lower())
        self.assertEqual(output.strip(), email.body.strip())

    def test_repairs_downgraded_score_lamp_and_flare_in_place_per_user_and_chart(self):
        user = create_user(player_id="p_affected", with_django_user=True)
        other_user = create_user(player_id="p_other", with_django_user=True)
        song = create_song(id="song_rep", title="Repair Song")
        chart1 = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)
        chart2 = create_chart(song=song, difficulty=Difficulty.objects.get(id=4), rating=17)

        # Chart 1: historical play had higher score (960000), higher lamp (4), and flare_gauge=7;
        # Current Score was downgraded to score=910000, clear_type=2, flare_gauge=None.
        create_user_score(user=user, chart=chart1, score=960000, clear_type=3, flare_gauge=None, current=None, timestamp=100)
        create_user_score(user=user, chart=chart1, score=900000, clear_type=4, flare_gauge=7, current=None, timestamp=200)
        current1 = create_user_score(user=user, chart=chart1, score=910000, clear_type=2, flare_gauge=None, current=True, timestamp=300)

        # Chart 2: flare_gauge was downgraded from 0 to None (0 must be treated as valid, not falsy)
        create_user_score(user=user, chart=chart2, score=930000, clear_type=3, flare_gauge=0, current=None, timestamp=150)
        current2 = create_user_score(user=user, chart=chart2, score=930000, clear_type=3, flare_gauge=None, current=True, timestamp=250)

        # Another user has higher values on chart2; must not affect `user`
        create_user_score(user=other_user, chart=chart2, score=999000, clear_type=5, flare_gauge=9, current=True, timestamp=400)

        total_before = UserScore.objects.count()
        self._run_forward()

        self.assertEqual(UserScore.objects.count(), total_before)

        current1.refresh_from_db()
        self.assertTrue(current1.current)
        self.assertEqual(current1.score, 960000)
        self.assertEqual(current1.clear_type, 4)
        self.assertEqual(current1.flare_gauge, 7)
        self.assertEqual(current1.timestamp, 300)

        current2.refresh_from_db()
        self.assertEqual(current2.score, 930000)
        self.assertEqual(current2.clear_type, 3)
        self.assertEqual(current2.flare_gauge, 0)

    def test_recomputes_normalized_and_quality_using_frozen_formulas(self):
        user = create_user(player_id="p_formulas", with_django_user=True)
        song = create_song(id="song_formulas", title="Formula Song")
        bps_norm = json.dumps([-10.0, -6.0, -2.323])
        bps_qual = json.dumps([10.0, 14.0, 20.0])

        chart_cleared = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=1),
            rating=12,
            normscore_breakpoints=bps_norm,
            quality_breakpoints=bps_qual,
        )
        chart_mfc = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=2),
            rating=13,
            normscore_breakpoints=bps_norm,
            quality_breakpoints=bps_qual,
        )
        chart_failed = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=3),
            rating=14,
            normscore_breakpoints=bps_norm,
            quality_breakpoints=bps_qual,
        )
        chart_no_bps = create_chart(
            song=song,
            difficulty=Difficulty.objects.get(id=4),
            rating=15,
            normscore_breakpoints="",
            quality_breakpoints="",
        )

        # 1. Cleared chart: 999,744 -> diff 256 -> normalized -8.0 -> midpoint quality 12.0
        create_user_score(user=user, chart=chart_cleared, score=999744, clear_type=3, current=None)
        cur_cleared = create_user_score(
            user=user, chart=chart_cleared, score=998976, clear_type=3,
            normalized=-10.0, quality=10.0, current=True,
        )

        # 2. MFC chart: 1,000,000 -> normalized -2.323 -> quality 20.0
        create_user_score(user=user, chart=chart_mfc, score=1000000, clear_type=5, current=None)
        cur_mfc = create_user_score(
            user=user, chart=chart_mfc, score=998976, clear_type=4,
            normalized=-10.0, quality=10.0, current=True,
        )

        # 3. Failed chart (lamp=0): score repaired to 999,744 -> normalized -8.0, quality stays None
        create_user_score(user=user, chart=chart_failed, score=999744, clear_type=0, current=None)
        cur_failed = create_user_score(
            user=user, chart=chart_failed, score=998976, clear_type=0,
            normalized=-10.0, quality=99.0, current=True,
        )

        # 4. Cleared chart without breakpoints: score repaired to 999,744 -> normalized -8.0, quality None
        create_user_score(user=user, chart=chart_no_bps, score=999744, clear_type=2, current=None)
        cur_no_bps = create_user_score(
            user=user, chart=chart_no_bps, score=998976, clear_type=2,
            normalized=-10.0, quality=None, current=True,
        )

        self._run_forward()

        cur_cleared.refresh_from_db()
        self.assertAlmostEqual(cur_cleared.normalized, -8.0, places=6)
        self.assertAlmostEqual(cur_cleared.quality, 12.0, places=6)

        cur_mfc.refresh_from_db()
        self.assertAlmostEqual(cur_mfc.normalized, -2.323, places=6)
        self.assertAlmostEqual(cur_mfc.quality, 20.0, places=6)

        cur_failed.refresh_from_db()
        self.assertAlmostEqual(cur_failed.normalized, -8.0, places=6)
        self.assertIsNone(cur_failed.quality)

        cur_no_bps.refresh_from_db()
        self.assertAlmostEqual(cur_no_bps.normalized, -8.0, places=6)
        self.assertIsNone(cur_no_bps.quality)

    def test_affected_report_email_and_stdout_list_users_charts_and_changed_fields(self):
        affected_user = create_user(player_id="pid_123", with_django_user=True)
        unlinked_user = create_user(player_id="pid_no_dj", with_django_user=False)
        unaffected_user = create_user(player_id="pid_clean", with_django_user=True)

        song = create_song(id="song_report", title="MAX 300")
        expert = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=15)
        challenge = create_chart(song=song, difficulty=Difficulty.objects.get(id=4), rating=18)

        # Affected user: score + flare changed on expert; lamp unchanged (3)
        create_user_score(user=affected_user, chart=expert, score=980000, clear_type=3, flare_gauge=8, current=None)
        create_user_score(user=affected_user, chart=expert, score=940000, clear_type=3, flare_gauge=None, current=True)

        # Unlinked user (django_user=None): lamp changed on challenge
        create_user_score(user=unlinked_user, chart=challenge, score=910000, clear_type=4, current=None)
        create_user_score(user=unlinked_user, chart=challenge, score=910000, clear_type=2, current=True)

        # Unaffected user: should not appear in report
        create_user_score(user=unaffected_user, chart=expert, score=990000, clear_type=4, current=True)

        with self.settings(MAINTAINER_EMAIL="maintainer@example.com"):
            output = self._run_forward()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["maintainer@example.com"])

        body = email.body
        self.assertEqual(output.strip(), body.strip())

        self.assertIn(affected_user.django_user.username, body)
        self.assertIn("pid_123", body)
        self.assertIn("MAX 300", body)
        self.assertIn("Expert", body)
        self.assertIn("940000 -> 980000", body)
        self.assertIn("None -> 8", body)

        self.assertIn("pid_no_dj", body)
        self.assertIn("Challenge", body)
        self.assertIn("2 -> 4", body)

        self.assertNotIn("pid_clean", body)

    def test_email_delivery_failure_logs_error_and_preserves_db_repair(self):
        user = create_user(player_id="pid_mail_fail", with_django_user=True)
        song = create_song(id="song_mail_fail", title="Mail Fail Song")
        chart = create_chart(song=song, difficulty=Difficulty.objects.get(id=3), rating=14)

        create_user_score(user=user, chart=chart, score=960000, clear_type=4, current=None)
        current = create_user_score(user=user, chart=chart, score=920000, clear_type=3, current=True)

        with patch(
            "django.core.mail.backends.locmem.EmailBackend.send_messages",
            side_effect=OSError("SMTP connection refused"),
        ):
            output = self._run_forward()

        current.refresh_from_db()
        self.assertEqual(current.score, 960000)
        self.assertEqual(current.clear_type, 4)
        self.assertIn("Mail Fail Song", output)
        self.assertIn("SMTP connection refused", output)
