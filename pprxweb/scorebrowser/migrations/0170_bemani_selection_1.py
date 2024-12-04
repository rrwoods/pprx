from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).filter(hidden=False).order_by("difficulty_id")
        if candidates.count() == 0:
            raise ValueError("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def createExtraSaviors(event, title):
        for chart in findCharts(title):
            task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=createExtraSaviors.nextOrdering)
            ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            createExtraSaviors.nextOrdering += 10
    createExtraSaviors.nextOrdering = 0

    ordering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10
    phase1 = UnlockEvent.objects.create(
        version_id=20,
        group = UnlockGroup.objects.get(name="Extra Savior"),
        name = "BEMANI SELECTION vol.1 phase 1 songs",
        ordering = ordering,
    )
    createExtraSaviors(phase1, "Beyond The Earth")
    createExtraSaviors(phase1, "Red. by Full Metal Jacket")
    createExtraSaviors(phase1, "TYCOON")
    createExtraSaviors(phase1, "雪上断火")
    createExtraSaviors(phase1, "罪と罰")

    ordering += 10
    phase2 = UnlockEvent.objects.create(
        version_id=20,
        group = UnlockGroup.objects.get(name="Extra Savior"),
        name = "BEMANI SELECTION vol.1 phase 2 songs",
        ordering = ordering,
    )
    createExtraSaviors(phase2, "DIAVOLO")
    createExtraSaviors(phase2, "Fly Like You")
    createExtraSaviors(phase2, "quaver♪")
    createExtraSaviors(phase2, "蛇神")
    createExtraSaviors(phase2, "逆月")


def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0168_gp_33_34_jubeat_3_gl_rotate_hyperdrive'),
    ]

    operations = [migrations.RunPython(forward, backward)]