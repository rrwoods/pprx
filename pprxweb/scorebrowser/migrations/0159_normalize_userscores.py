# Generated by Django 4.2.7 on 2024-09-27 02:43

from django.db import migrations
import math

def forward(apps, schema_editor):
    UserScore = apps.get_model("scorebrowser", "UserScore")

    all_scores = UserScore.objects.all()
    remaining = all_scores.count()
    batch = []
    for score in all_scores:
        score.normalized = -2.323 if score.score == 1000000 else -math.log2(1000000 - score.score)
        batch.append(score)
        remaining -= 1
        if len(batch) == 1000:
            print("Updating batch...")
            UserScore.objects.bulk_update(batch, ['normalized'])
            print("...{} remaining.".format(remaining))
            batch = []

    if batch:
        print("Final batch...")
        UserScore.objects.bulk_update(batch, ['normalized'])


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0158_userscore_normalized_delete_unprocessedpair'),
    ]

    operations = [migrations.RunPython(forward, backward)]
