from django.db import migrations
from django.db.models import Max

def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    SongLock = apps.get_model("scorebrowser", "SongLock")

    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
    def gpPack(packName, titles):
        gpPack.nextOrdering += 10
        pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=gpPack.nextOrdering)

        for title in titles:
            for difficulty_id in range(4):
                chart = findChart(title, difficulty_id)
                ChartUnlock.objects.create(task=pack, chart=chart)

        return pack
    gpPack.nextOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']

    def newChallengeChart(title):
        newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
        newChart = UnlockTask.objects.create(event=newChallengeChartsEvent, name="{} Challenge".format(title), ordering=20)
        chart = findChart(title, 4)
        ChartUnlock.objects.create(task=newChart, chart=chart)
        return chart

    def gpChallenge(packs, charts):
        for pack in packs:
            for chart in charts:
                ChartUnlock.objects.create(task=pack, chart=chart)

    vol25 = gpPack("GRAND PRIX music pack vol.25", [])
    vol26 = gpPack("GRAND PRIX music pack vol.26", [])
    gpChallenge([vol25, vol26], [newChallengeChart("HAPPY☆LUCKY☆YEAPPY"), newChallengeChart("恋愛観測")])

    SongLock.objects.get(song__title="Sector").delete()
    SongLock.objects.get(song__title="Ability").delete()
    SongLock.objects.get(song__title="SURVIVAL AT THE END OF THE UNIVERSE").delete()
    SongLock.objects.get(song__title="Jungle Dance").delete()
    SongLock.objects.get(song__title="Rave in the Shell").delete()
    SongLock.objects.get(song__title="Not Alone").delete()
    SongLock.objects.get(song__title="GROOVE 04").delete()
    SongLock.objects.get(song__title="Euphoric Fragmentation").delete()
    SongLock.objects.get(song__title="Continue to the real world?").delete()
    SongLock.objects.get(song__title="9th Outburst").delete()
    SongLock.objects.get(song__title="My Drama").delete()

def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0137_world_unlock_purge'),
    ]

    operations = [migrations.RunPython(forward, backward)]
