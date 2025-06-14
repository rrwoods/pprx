# Generated by Django 4.2.7 on 2025-04-02 04:58

from django.db import migrations


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

    limitedEvents = UnlockGroup.objects.get(name="Time-limited events")
    def galaxyBrave(trialName, title):
        galaxyBrave.eventOrdering += 10
        trial = UnlockEvent.objects.create(
           version_id=20,
           group=limitedEvents,
           name=trialName,
           progressive=True,
           ordering=galaxyBrave.eventOrdering,
           amethyst_required=False, 
        )
        for diff in range(5):
            chart = findChart(title, diff)
            task = UnlockTask.objects.create(
                event=trial,
                name="{} ({})".format(title, Difficulty.objects.get(id=diff).name),
                ordering=diff*10,
            )
            ChartUnlock.objects.create(task=task, chart=chart)
    galaxyBrave.eventOrdering = UnlockEvent.objects.filter(group=limitedEvents).aggregate(Max('ordering'))['ordering__max']
    galaxyBrave("GALAXY BRAVE: MOUNTAIN", "Eira")

    gpAdvance = UnlockEvent.objects.get(name='GRAND PRIX Advance Play')
    def gpPack(packName, titles):
        gpPack.nextOrdering += 10
        pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=gpPack.nextOrdering)

        for title in titles:
            for difficulty_id in range(4):
                chart = findChart(title, difficulty_id)
                ChartUnlock.objects.create(task=pack, chart=chart)

        return pack
    gpPack.nextOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']

    def gpChallenge(packs, charts):
        for pack in packs:
            for chart in charts:
                ChartUnlock.objects.create(task=pack, chart=chart)

    vol35 = gpPack("GRAND PRIX music pack vol.35", ["Couleur=Blanche"])
    gpChallenge([vol35], [
        findChart("Lose Your Sense", 4),
        findChart("[ ]DENTITY", 4),
    ])

    bemani3 = gpPack("BEMANI SELECTION music pack vol.3", [])
    gpChallenge([bemani3], [
        findChart("勇猛無比", 4),
        findChart("Riot of Color", 4),
        findChart("Get Back Up!", 4),
    ])

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).order_by('difficulty_id')
        if len(candidates) == 0:
            raise Exception("No charts for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    advanceBorder = UnlockTask.objects.create(event=UnlockEvent.objects.get(name="WORLD LEAGUE"), name="GOLD CLASS with advanced border", ordering=40)
    def newGoldenLeague(new_title):
        for c in findCharts(new_title):
            ChartUnlock.objects.create(task=advanceBorder, chart=c)

    newGoldenLeague('まにぃまにあ××')


def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0178_triple_tribe_2_es_convert'),
    ]

    operations = [migrations.RunPython(forward, backward)]
