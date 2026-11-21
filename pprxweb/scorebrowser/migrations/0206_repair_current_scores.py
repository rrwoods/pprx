import json
import math
import numpy as np

from django.conf import settings
from django.core.mail import send_mail
from django.db import migrations, transaction
from django.db.models import Max


def _compute_normalized_score(score):
    if score >= 1000000:
        return -2.323
    return -math.log2(1000000 - score)


def _compute_quality(score, lamp, chart):
    if lamp <= 0:
        return None
    if not chart.normscore_breakpoints or not chart.quality_breakpoints:
        return None
    try:
        norm_bps = json.loads(chart.normscore_breakpoints)
        qual_bps = json.loads(chart.quality_breakpoints)
        if not norm_bps or not qual_bps or len(norm_bps) != len(qual_bps):
            return None
        norm_score = _compute_normalized_score(score)
        return float(np.interp(norm_score, norm_bps, qual_bps))
    except (ValueError, TypeError):
        return None


def forward(apps, schema_editor=None):
    UserScore = apps.get_model("scorebrowser", "UserScore")

    max_by_user_chart = {
        (row["user_id"], row["chart_id"]): row
        for row in UserScore.objects.values("user_id", "chart_id").annotate(
            max_score=Max("score"),
            max_clear_type=Max("clear_type"),
            max_flare_gauge=Max("flare_gauge"),
        )
    }

    current_scores = (
        UserScore.objects
        .filter(current=True)
        .select_related("user__django_user", "chart__song", "chart__difficulty")
        .order_by("user_id", "chart_id", "id")
    )

    scores_to_update = []
    report_by_user = {}
    for current in current_scores:
        agg = max_by_user_chart[(current.user_id, current.chart_id)]
        new_score = max(current.score, agg["max_score"])
        new_lamp = max(current.clear_type, agg["max_clear_type"])
        changes = []
        if new_score > current.score:
            changes.append(f"score: {current.score} -> {new_score}")
        if new_lamp > current.clear_type:
            changes.append(f"lamp: {current.clear_type} -> {new_lamp}")

        max_flare = agg["max_flare_gauge"]
        new_flare = current.flare_gauge
        if max_flare is not None and (current.flare_gauge is None or max_flare > current.flare_gauge):
            new_flare = max_flare
            changes.append(f"flare_gauge: {current.flare_gauge} -> {new_flare}")

        if changes:
            user = current.user
            if user.id not in report_by_user:
                username = user.django_user.username if user.django_user is not None else "(no django user)"
                report_by_user[user.id] = {
                    "header": f"User: {username} (player_id: {user.player_id})",
                    "lines": [],
                }
            chart = current.chart
            chart_label = f"{chart.song.title} [{chart.difficulty.name}] (chart_id={chart.id})"
            report_by_user[user.id]["lines"].append(f"  - {chart_label}: {', '.join(changes)}")

            current.score = new_score
            current.clear_type = new_lamp
            current.flare_gauge = new_flare
            current.normalized = _compute_normalized_score(new_score)
            current.quality = _compute_quality(new_score, new_lamp, current.chart)
            scores_to_update.append(current)

    if scores_to_update:
        with transaction.atomic():
            UserScore.objects.bulk_update(
                scores_to_update,
                ["score", "clear_type", "flare_gauge", "normalized", "quality"],
                batch_size=500,
            )

    if not scores_to_update:
        report = (
            "PPR X Current Score repair report:\n"
            "0 users and 0 Current Score rows were affected."
        )
        subject = "PPR X score repair report: 0 rows affected"
    else:
        lines = [
            "PPR X Current Score repair report:",
            f"Affected users: {len(report_by_user)}, repaired Current Score rows: {len(scores_to_update)}",
        ]
        for entry in report_by_user.values():
            lines.append("")
            lines.append(entry["header"])
            lines.extend(entry["lines"])
        report = "\n".join(lines)
        subject = (
            f"PPR X score repair report: {len(report_by_user)} user(s), "
            f"{len(scores_to_update)} row(s) repaired"
        )

    print(report)
    try:
        send_mail(
            subject,
            report,
            "pprx.gg@gmail.com",
            [settings.MAINTAINER_EMAIL],
            fail_silently=False,
        )
    except Exception as exc:
        print(f"Failed to send repair report email: {exc}")


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0205_remove_user_pulling_scores_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
