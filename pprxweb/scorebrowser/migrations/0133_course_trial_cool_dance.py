from django.db import migrations, models
from django.db.models import Max

def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def courseTrial(course_name, title):
        courseTrialA3 = UnlockEvent.objects.filter(name="COURSE TRIAL A3").first()
        lastOrdering = UnlockTask.objects.filter(event=courseTrialA3).aggregate(Max('ordering'))['ordering__max']

        task = UnlockTask.objects.create(event=courseTrialA3, name="{} (unlocks {})".format(course_name, title), ordering=lastOrdering+10)
        for chart in findCharts(title):
            ChartUnlock.objects.create(task=task, chart=chart)

    courseTrial("COOL DANCE!", "melody H4CKER")

def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [('scorebrowser', '0132_gp_17_18_unlocked')]

    operations = [migrations.RunPython(forward, backward)]
