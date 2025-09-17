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

    chart3 = gpPack("chart pack vol.3", [])
    gpChallenge([chart3], [
        findChart("Blind Justice ～Torn souls, Hurt Faiths ～", 4),
        findChart("BURNIN' THE FLOOR", 4),
        findChart("Destiny lovers", 4),
        findChart("JET WORLD", 4),
        findChart("LOVE♥SHINE", 4),
        findChart("Music In The Rhythm", 4),
        findChart("SEXY PLANET", 4),
        findChart("The Least 100sec", 4),
        findChart("think ya better D", 4),
        findChart("TRIP MACHINE ～luv mix～", 4),
    ])

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).order_by("difficulty_id")
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def createExtraSaviors(event, title):
        for chart in findCharts(title):
            task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=createExtraSaviors.nextOrdering)
            ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            createExtraSaviors.nextOrdering += 10
    createExtraSaviors.nextOrdering = 0

    ordering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10
    extraSavior = UnlockGroup.objects.get(name="Extra Savior")
    audition = UnlockEvent.objects.create(
        version_id=20,
        group=extraSavior,
        name="The 3rd MUSIC CREATOR AUDITION",
        ordering=ordering,
    )
    createExtraSaviors(audition, "Autosummer")
    createExtraSaviors(audition, "Burstix Comet")
    createExtraSaviors(audition, "Collapse of the Sanctuary")

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
    rotate(["Florence"], ["S.O.D"], ["Is this dance a Hakken?"], [])

    advanceBorder = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="GOLD CLASS with advanced border")
    def newGoldenLeague(new_title):
        for c in findCharts(new_title):
            ChartUnlock.objects.create(task=advanceBorder, chart=c)
    newGoldenLeague("BRAIN-HEART")

    UnlockTask.objects.get(name="music pack vol.29").delete()
    UnlockTask.objects.get(name="music pack vol.30").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.5").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.6").delete()

def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0193_extra_saviors'),
    ]

    operations = [migrations.RunPython(forward, backward)]
