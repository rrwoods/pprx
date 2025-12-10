from django.db import migrations
from django.db.models import Max



def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    Difficulty = apps.get_model("scorebrowser", "Difficulty")


    UnlockTask.objects.get(name="SPECIAL music pack feat.jubeat vol.3").delete()

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

    def gpChallenge(packs, titles):
        for pack in packs:
            for title in titles:
                chart = findChart(title, 4)
                ChartUnlock.objects.create(task=pack, chart=chart)    

    touhou7 = gpPack("SPECIAL music pack feat.Touhou Project vol.7", [
        "4NT1 D34D",
        "Deadly Dolly Dance",
        "SkyDrive! (HASEKO EUROBEAT MIX)",
        "東方妖々夢 ULTIMATE MEDLEY",
    ])
    gpChallenge([touhou7], [
        "SkyDrive! (HASEKO EUROBEAT MIX)",
        "東方妖々夢 ULTIMATE MEDLEY",
    ])

    newBraves = [
        ("GALAXY BRAVE: UNSTABLE", "迷宮のロンド"),
        ("GALAXY BRAVE: BREAKTHROUGH", "New Millennium Pt.2"),
        ("GALAXY BRAVE: BLAZING", "鳳 (Five Flares Mix)"),
    ]
    limited = UnlockGroup.objects.get(name="Time-limited events")
    eventOrdering = UnlockEvent.objects.filter(group=limited).aggregate(Max('ordering'))['ordering__max']
    for newBrave in newBraves:
        eventOrdering += 20
        brave = UnlockEvent.objects.create(
            version_id=20,
            group=limited,
            name=newBrave[0],
            progressive=True,
            ordering=eventOrdering,
            amethyst_required=False,
        )
        for diff in range(5):
            chart = findChart(newBrave[1], diff)
            task = UnlockTask.objects.create(
                event=brave,
                name="{} ({})".format(newBrave[1], Difficulty.objects.get(id=diff).name),
                ordering=diff*10,
            )
            ChartUnlock.objects.create(task=task, chart=chart)

def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0195_chartpack4_mysticalreunionconvert'),
    ]

    operations = [migrations.RunPython(forward, backward)]
