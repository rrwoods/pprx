from django.db import migrations
from django.db.models import Max

def forward(apps, schema_editor):
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    worldLeague = UnlockEvent.objects.get(name="WORLD LEAGUE")
    goldClass = UnlockTask.objects.get(name="GOLD CLASS", event=worldLeague)
    for chart in findCharts("access super [hyper] focus"):
        ChartUnlock.objects.create(task=goldClass, chart=chart)


    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    def createChallengeExtraSavior(event, title):
        chart = findChart(title, 4)
        task = UnlockTask.objects.create(event=event, name='{} (Challenge {})', ordering=createChallengeExtraSavior.nextOrdering)
        ChartUnlock.objects.create(task=task, chart=chart, extra=True)
        createChallengeExtraSavior.nextOrdering += 10
    createChallengeExtraSavior.nextOrdering = 0

    extra_savior = UnlockGroup.objects.get(name="Extra Savior")
    eventOrdering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10
    phase1 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st CLASSIC CHALLENGE phase 1",
        ordering=eventOrdering,
    )
    createChallengeExtraSavior(phase1, "BE LOVIN")
    createChallengeExtraSavior(phase1, "Holic")
    createChallengeExtraSavior(phase1, "華爛漫 -Flowers-")

    eventOrdering += 10
    phase2 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st CLASSIC CHALLENGE phase 2",
        ordering=eventOrdering,
    )
    createChallengeExtraSavior(phase2, "PARANOIA EVOLUTION")

    eventOrdering += 10
    phase3 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st CLASSIC CHALLENGE phase 3",
        ordering=eventOrdering,
    )
    createChallengeExtraSavior(phase3, "Übertreffen")


    UnlockTask.objects.get(name="GRAND PRIX music pack vol.23").delete()
    UnlockTask.objects.get(name="GRAND PRIX music pack vol.24").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.HinaBitter♪ vol.1").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.HinaBitter♪ vol.2").delete()




def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0172_gl_new_hakken'),
    ]


    operations = [migrations.RunPython(forward, backward)]