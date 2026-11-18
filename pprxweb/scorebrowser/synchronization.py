from dataclasses import dataclass
from enum import Enum
import json
import math
from typing import Optional, Protocol
import numpy as np

from django.db import transaction

from .misc import sort_key
from .models import (
    Chart,
    ChartUnlock,
    Song,
    UnlockTask,
    User,
    UserScore,
)


@dataclass(frozen=True)
class UpstreamScore:
    song_id: str
    difficulty: int
    rating: int
    song_title: str
    score: int
    lamp: int
    timestamp: int
    flare_gauge: Optional[int] = None


class UpstreamScoreSource(Protocol):
    def fetch_scores(self, user: User) -> list[UpstreamScore]:
        ...


class SynchronizationError(Exception):
    pass


class ReauthRequired(SynchronizationError):
    pass


class UpstreamError(SynchronizationError):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Upstream error {status}: {body}")


class SynchronizationOutcome(str, Enum):
    SYNCHRONIZED = "SYNCHRONIZED"
    ALREADY_RUNNING = "ALREADY_RUNNING"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


@dataclass(frozen=True)
class SynchronizationResult:
    outcome: SynchronizationOutcome
    new_scores: int = 0
    superseded_scores: int = 0
    corrected_fields: int = 0
    status_code: Optional[int] = None
    error_body: Optional[str] = None


def compute_normalized_score(score: int) -> float:
    if score >= 1000000:
        return -2.323
    return -math.log2(1000000 - score)


def compute_quality(score: int, lamp: int, chart: Chart) -> Optional[float]:
    if lamp <= 0:
        return None
    if not chart.normscore_breakpoints or not chart.quality_breakpoints:
        return None
    try:
        norm_bps = json.loads(chart.normscore_breakpoints)
        qual_bps = json.loads(chart.quality_breakpoints)
        if not norm_bps or not qual_bps or len(norm_bps) != len(qual_bps):
            return None
        norm_score = compute_normalized_score(score)
        return float(np.interp(norm_score, norm_bps, qual_bps))
    except (ValueError, TypeError):
        return None


def _build_user_score(user: User, chart: Chart, score: int, lamp: int, flare: Optional[int], timestamp: int) -> UserScore:
    return UserScore(
        user=user,
        chart=chart,
        score=score,
        normalized=compute_normalized_score(score),
        quality=compute_quality(score, lamp, chart),
        clear_type=lamp,
        flare_gauge=flare,
        timestamp=timestamp,
        current=True,
    )


def synchronize(user: User, source: Optional[UpstreamScoreSource] = None) -> SynchronizationResult:
    if source is None:
        raise NotImplementedError("Production 3icecream adapter is implemented in #75")

    try:
        upstream_scores = source.fetch_scores(user)
    except ReauthRequired:
        user.reauth = True
        user.save(update_fields=['reauth'])
        return SynchronizationResult(outcome=SynchronizationOutcome.REAUTH_REQUIRED)
    except UpstreamError as exc:
        print(f"Synchronization failed: upstream error {exc.status}: {exc.body}")
        return SynchronizationResult(
            outcome=SynchronizationOutcome.UPSTREAM_ERROR,
            status_code=exc.status,
            error_body=exc.body,
        )

    # Ingest upstream scores
    challenge_task = UnlockTask.objects.filter(name="New Challenge charts (A3+)").first()
    all_charts = {(chart.song_id, chart.difficulty_id): chart for chart in Chart.objects.all().select_related('song')}
    all_song_ids = set(Song.objects.values_list('id', flat=True))

    scores_lookup: dict[tuple[str, int], UpstreamScore] = {}
    for score in upstream_scores:
        if score.difficulty > 4:
            continue
        key = (score.song_id, score.difficulty)
        if key in scores_lookup:
            prev = scores_lookup[key]
            merged_score = max(prev.score, score.score)
            merged_lamp = max(prev.lamp, score.lamp)
            if score.flare_gauge is None:
                merged_flare = prev.flare_gauge
            elif prev.flare_gauge is None:
                merged_flare = score.flare_gauge
            else:
                merged_flare = max(prev.flare_gauge, score.flare_gauge)
            latest_timestamp = max(prev.timestamp, score.timestamp)
            scores_lookup[key] = UpstreamScore(
                song_id=score.song_id,
                difficulty=score.difficulty,
                rating=score.rating,
                song_title=score.song_title,
                score=merged_score,
                lamp=merged_lamp,
                timestamp=latest_timestamp,
                flare_gauge=merged_flare,
            )
        else:
            scores_lookup[key] = score

        if key not in all_charts:
            if score.song_id not in all_song_ids:
                song = Song.objects.create(
                    id=score.song_id,
                    version_id=20,
                    title=score.song_title,
                    sort_key=sort_key(score.song_title),
                )
                all_song_ids.add(score.song_id)
            else:
                song = Song.objects.get(id=score.song_id)

            with transaction.atomic():
                chart = Chart.objects.create(
                    song_id=score.song_id,
                    difficulty_id=score.difficulty,
                    rating=score.rating,
                    hidden=True,
                )
                if score.difficulty == 4 and song.version_id <= 18 and challenge_task is not None:
                    ChartUnlock.objects.create(task=challenge_task, chart=chart)
                chart.song = song
                all_charts[key] = chart

    current_scores: dict[int, UserScore] = {
        s.chart_id: s for s in UserScore.objects.filter(user=user, current=True)
    }

    formerly_current_scores: list[UserScore] = []
    new_scores: list[UserScore] = []
    new_scores_count = 0
    superseded_scores_count = 0
    corrected_fields_count = 0

    for key, upstream in scores_lookup.items():
        chart = all_charts[key]
        old_score = current_scores.get(chart.id)

        if old_score is not None:
            merged_score = max(old_score.score, upstream.score)
            merged_lamp = max(old_score.clear_type, upstream.lamp)
            if upstream.flare_gauge is None:
                merged_flare = old_score.flare_gauge
            elif old_score.flare_gauge is None:
                merged_flare = upstream.flare_gauge
            else:
                merged_flare = max(old_score.flare_gauge, upstream.flare_gauge)

            if upstream.score < old_score.score:
                print(f"Upstream score {upstream.score} lower than stored {old_score.score} on chart {chart.id} for user {user.id}")
                corrected_fields_count += 1
            if upstream.lamp < old_score.clear_type:
                print(f"Upstream lamp {upstream.lamp} lower than stored {old_score.clear_type} on chart {chart.id} for user {user.id}")
                corrected_fields_count += 1
            if old_score.flare_gauge is not None:
                if upstream.flare_gauge is None or upstream.flare_gauge < old_score.flare_gauge:
                    print(f"Upstream flare {upstream.flare_gauge} lower than stored {old_score.flare_gauge} on chart {chart.id} for user {user.id}")
                    corrected_fields_count += 1

            improved = (
                (merged_score > old_score.score) or
                (merged_lamp > old_score.clear_type) or
                (merged_flare is not None and (old_score.flare_gauge is None or merged_flare > old_score.flare_gauge))
            )

            if improved:
                old_score.current = None
                formerly_current_scores.append(old_score)
                superseded_scores_count += 1

                new_scores.append(
                    _build_user_score(
                        user=user,
                        chart=chart,
                        score=merged_score,
                        lamp=merged_lamp,
                        flare=merged_flare,
                        timestamp=upstream.timestamp,
                    )
                )
        else:
            new_scores_count += 1
            new_scores.append(
                _build_user_score(
                    user=user,
                    chart=chart,
                    score=upstream.score,
                    lamp=upstream.lamp,
                    flare=upstream.flare_gauge,
                    timestamp=upstream.timestamp,
                )
            )

    if formerly_current_scores or new_scores:
        with transaction.atomic():
            if formerly_current_scores:
                UserScore.objects.bulk_update(formerly_current_scores, ['current'])
            if new_scores:
                UserScore.objects.bulk_create(new_scores)

    return SynchronizationResult(
        outcome=SynchronizationOutcome.SYNCHRONIZED,
        new_scores=new_scores_count,
        superseded_scores=superseded_scores_count,
        corrected_fields=corrected_fields_count,
    )
