from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    Difficulty = apps.get_model("scorebrowser", "Difficulty")

    limited = UnlockGroup.objects.get(name="Time-limited events")
    platinumEvent = UnlockEvent.objects.create(
        version_id=20,
        group=limited,
        name="PLATINUM MEMBER PASS",
        ordering=-100,
        amethyst_required=False,
    )
    platinumTask = UnlockTask.objects.create(
        event=platinumEvent,
        name="Purchased",
        ordering=0,
    )

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    for title in ["Monsters Den", "Stand Alone Beat Masta"]:
        for chart in findCharts(title):
            ChartUnlock.objects.create(task=platinumTask, chart=chart)


    gpAdvance = UnlockEvent.objects.get(name='GRAND PRIX Advance Play')
    def gpPackWithChallenge(packName, titles):
        gpPackWithChallenge.nextOrdering += 10
        pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=gpPackWithChallenge.nextOrdering)
        for title in titles:
            for chart in findCharts(title):
                ChartUnlock.objects.create(task=pack, chart=chart)
        return pack
    gpPackWithChallenge.nextOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']

    gpPackWithChallenge("music pack vol.36", [
        "EBONY & IVORY",
        "ARACHNE",
        "Liar×Girl",
        "絶対零度",
    ])
    gpPackWithChallenge("SPECIAL music pack feat.pop'n music vol.1", [
        "路男",
        "明鏡止水",
        "ポチコの幸せな日常",
        "BabeL ～Next Story～",
    ])

    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    eventOrdering = UnlockEvent.objects.filter(group=limited).aggregate(Max('ordering'))['ordering__max']
    storm = UnlockEvent.objects.create(
       version_id=20,
       group=limited,
       name="GALAXY BRAVE: STORM",
       progressive=True,
       ordering=eventOrdering+10,
       amethyst_required=False, 
    )
    for diff in range(5):
        chart = findChart("Thunderstorm", diff)
        task = UnlockTask.objects.create(
            event=storm,
            name="Thunderstorm ({})".format(Difficulty.objects.get(id=diff).name),
            ordering=diff*10,
        )
        ChartUnlock.objects.create(task=task, chart=chart)

    def rotate(goldTitles, silverTitles, bronzeTitles, defaultTitles):
        bronze = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="BRONZE CLASS").id
        silver = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="SILVER CLASS").id
        gold = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="GOLD CLASS").id
        advance = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="GOLD CLASS with advanced border").id

        for goldTitle in goldTitles:
            goldUnlocks = ChartUnlock.objects.filter(task_id=advance, chart__song__title=goldTitle)
            for unlock in goldUnlocks:
                if unlock.chart.song.title == goldTitle:
                    unlock.task_id = gold
                    unlock.save()

        for silverTitle in silverTitles:
            silverUnlocks = ChartUnlock.objects.filter(task_id=gold, chart__song__title=silverTitle)
            for unlock in silverUnlocks:
                if unlock.chart.song.title == silverTitle:
                    unlock.task_id = silver
                    unlock.save()

        for bronzeTitle in bronzeTitles:
            bronzeUnlocks = ChartUnlock.objects.filter(task_id=silver, chart__song__title=bronzeTitle)
            for unlock in bronzeUnlocks:
                if unlock.chart.song.title == bronzeTitle:
                    unlock.task_id = bronze
                    unlock.save()

        for defaultTitle in defaultTitles:
            defaultUnlocks = ChartUnlock.objects.filter(task_id=bronze, chart__song__title=defaultTitle)
            for unlock in defaultUnlocks:
                if unlock.chart.song.title == defaultTitle:
                    unlock.delete()
    rotate([], ["まにぃまにあ××"], ["Time to HYPERDRIVE"], [])

    advanceBorder = UnlockTask.objects.create(event=UnlockEvent.objects.get(name="WORLD LEAGUE"), name="GOLD CLASS with advanced border", ordering=40)
    def newGoldenLeague(new_title):
        for c in findCharts(new_title):
            ChartUnlock.objects.create(task=advanceBorder, chart=c)
    newGoldenLeague("Florence")

def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0183_gp_25_26_unlocked'),
    ]

    operations = [migrations.RunPython(forward, backward)]
