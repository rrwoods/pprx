from django.db import migrations, models
from django.db.models import Max

def forward(apps, schema_editor):
    Cabinet = apps.get_model("scorebrowser", "Cabinet")
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")

    UnlockEvent.objects.filter(version_id=19).update(version_id=20)
    Cabinet.objects.filter(version_id=19).update(version_id=20)

    flareEvent = UnlockEvent.objects.create(
        version_id=20,
        group=UnlockGroup.objects.create(name="Flare Skill rank", ordering=35),
        name="Flare Skill rank",
        progressive=True,
        ordering=0,
    )

    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    def rankUnlock(points, title, difficulty_ids):
        task = UnlockTask.objects.create(event=flareEvent, name="{} points".format(points), ordering=points)
        for difficulty_id in difficulty_ids:
            ChartUnlock.objects.create(task=task, chart=findChart(title, difficulty_id))

    rankUnlock(2000, "極地大衝撃", [0, 1, 2])
    rankUnlock(4000, "HyperNOAH", [0, 1, 2])
    rankUnlock(6000, "WONDER COASTER", [0, 1, 2])
    rankUnlock(8000, "Gravity Collapse", [0, 1, 2])
    rankUnlock(10000, "Roche Limit", [0, 1, 2])
    rankUnlock(13000, "Ødyssey", [0, 1, 2])
    rankUnlock(16000, "極地大衝撃", [3])
    rankUnlock(20000, "HyperNOAH", [3])
    rankUnlock(24000, "WONDER COASTER", [3])
    rankUnlock(29000, "Gravity Collapse", [3])
    rankUnlock(34000, "Roche Limit", [3])
    rankUnlock(39500, "Ødyssey", [3])
    rankUnlock(45000, "Gravity Collapse", [4])
    rankUnlock(52500, "Roche Limit", [4])
    rankUnlock(60000, "Ødyssey", [4])

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

    drs1 = gpPack("SPECIAL music pack feat.DANCERUSH STARDOM vol.1", ["THE SAFARI (STARDOM Remix)"])
    drs2 = gpPack("SPECIAL music pack feat.DANCERUSH STARDOM vol.2", ["音楽 (STARDOM Remix)"])
    gpChallenge([drs1, drs2], [findChart("THE SAFARI (STARDOM Remix)", 4), findChart("音楽 (STARDOM Remix)", 4)])

    gpChallenge(
        [gpPack("music pack vol.27", []), gpPack("music pack vol.28", [])],
        [newChallengeChart("Drop The Bounce"), newChallengeChart("ミッドナイト☆WAR")]
    )
    gpChallenge(
        [gpPack("music pack vol.29", []), gpPack("music pack vol.30", [])],
        [newChallengeChart("F4SH10N"), newChallengeChart("Right Time Right Way")]
    )
    gpChallenge(
        [gpPack("SPECIAL music pack feat.Touhou Project vol.5", []), gpPack("SPECIAL music pack feat.Touhou Project vol.6", [])],
        [newChallengeChart("プレインエイジア -PHQ remix-"), newChallengeChart("月に叢雲華に風")]
    )

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        return [c for c in candidates if (c.song.title == title)]

    def createExtraSaviors(event, title):
        for chart in findCharts(title):
            # WHEN COPYING THIS METHOD, REORDER THE CHARTS BY DIFFICULTY_ID!
            task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=createExtraSaviors.nextOrdering)
            ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            createExtraSaviors.nextOrdering += 10
    createExtraSaviors.nextOrdering = 0

    extraSaviorWorld = UnlockEvent.objects.create(
        version_id=20,
        group = UnlockGroup.objects.get(name="Extra Savior"),
        name = "BEMANI×東方Project ～幻想郷音樂祭2024～",
        ordering = 0
    )
    createExtraSaviors(extraSaviorWorld, "SUPER HEROINE!!")
    createExtraSaviors(extraSaviorWorld, "弾幕信仰")
    createExtraSaviors(extraSaviorWorld, "残像ニ繋ガレタ追憶ノHIDEAWAY")

    newChallengeChart("Throw Out")

    checkYourLevelEvent = UnlockEvent.objects.create(
        version_id=20,
        name="LET'S CHECK YOUR LEVEL! Exclusive Song",
        ordering = 0
    )
    checkYourLevelTask = UnlockTask.objects.create(event=checkYourLevelEvent, name="LET'S CHECK YOUR LEVEL! Exclusive Song", ordering=0)
    ChartUnlock.objects.create(task=checkYourLevelTask, chart=findChart("Steps to the Star", 0))

def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0147_unlockevent_progressive'),
    ]

    operations = [migrations.RunPython(forward, backward)]
