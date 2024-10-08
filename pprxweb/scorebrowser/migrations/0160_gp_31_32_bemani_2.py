# Generated by Django 4.2.7 on 2024-10-02 02:19

from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    Song = apps.get_model("scorebrowser", "Song")
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

    def findSong(title):
        candidates = Song.objects.filter(title=title)
        for song in candidates:
            if song.title == title:
                return song

    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

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

    # It is fine to use this event, because the point is to lock them on A20Plus
    # There are no A3 cabs in the wild that we care about
    # If this comes back to bite me, I will run another migration to duplicate these into A3
    newChallengeChartsEvent = UnlockEvent.objects.get(name="New Challenge charts (A3)")
    def newChallengeChart(title):
        newChart = UnlockTask.objects.create(event=newChallengeChartsEvent, name="{} Challenge".format(title), ordering=20)
        chart = findChart(title, 4)
        ChartUnlock.objects.create(task=newChart, chart=chart)
        return chart

    def gpChallenge(packs, charts):
        for pack in packs:
            for chart in charts:
                ChartUnlock.objects.create(task=pack, chart=chart)

    gpChallenge([gpPack("BEMANI SELECTION music pack vol.2", [])], [
        newChallengeChart("If"),
        findChart("SAYONARA☆ディスコライト", 4),
        newChallengeChart("灼熱 Pt.2 Long Train Running"),
    ])

    vol31 = gpPack("music pack vol.31", [])
    vol32 = gpPack("music pack vol.32", ["Moving On", "BRE∀K DOWN! (World Version)", "No Matter What", "El ritmo te controla "])
    gpChallenge([vol31, vol32], [
        newChallengeChart("スーパー戦湯ババンバーン"),
        findChart("El ritmo te controla ", 4),
    ])



def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0159_normalize_userscores'),
    ]

    operations = [migrations.RunPython(forward, backward)]
