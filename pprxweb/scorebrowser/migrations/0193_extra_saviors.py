from django.db import migrations
from django.db.models import Max



def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    Difficulty = apps.get_model("scorebrowser", "Difficulty")

    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    def createChallengeExtraSavior(event, title):
        chart = findChart(title, 4)
        task = UnlockTask.objects.create(event=event, name='{} (Challenge {})'.format(title, chart.rating), ordering=createChallengeExtraSavior.nextOrdering)
        ChartUnlock.objects.create(task=task, chart=chart, extra=True)
        createChallengeExtraSavior.nextOrdering += 10
    createChallengeExtraSavior.nextOrdering = 0

    extra_savior = UnlockGroup.objects.get(name="Extra Savior")
    eventOrdering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10
    white = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st WHITE CHALLENGE",
        ordering=eventOrdering,
    )
    createChallengeExtraSavior(white, "In The Breeze")
    createChallengeExtraSavior(white, "クリムゾンゲイト")
    createChallengeExtraSavior(white, "パ→ピ→プ→Yeah!")
    createChallengeExtraSavior(white, "True Blue")
    createChallengeExtraSavior(white, "Remain")


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0192_20250810_content'),
    ]

    operations = [migrations.RunPython(forward, backward)]
