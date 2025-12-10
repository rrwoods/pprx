# re-adding an overzealously-deleted unlock ...




from django.db import migrations


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
    gpAdvance = UnlockEvent.objects.get(name='GRAND PRIX Advance Play')

    def gpPack(packName, titles):
        pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=0)

        for title in titles:
            for difficulty_id in range(4):
                chart = findChart(title, difficulty_id)
                ChartUnlock.objects.create(task=pack, chart=chart)

        return pack

    def gpChallenge(packs, titles):
        for pack in packs:
            for title in titles:
                chart = findChart(title, 4)
                ChartUnlock.objects.create(task=pack, chart=chart)

    jubeat3 = gpPack("SPECIAL music pack feat.jubeat vol.3", ["1116", "Sahara"])
    gpChallenge([jubeat3], ["1116"])





def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0197_alter_unlockevent_amethyst_required'),
    ]

    operations = [migrations.RunPython(forward, backward)]
