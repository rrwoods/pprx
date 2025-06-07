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

    reflec = gpPack("SPECIAL music pack feat.REFLEC BEAT vol.3", [
        "Gale Rider",
        "Hollywood Galaxy",
    ])
    gpChallenge([reflec], [findChart("リリーゼと炎龍レーヴァテイン", 4)])

    hinabitter = gpPack("SPECIAL music pack feat.HinaBitter♪ vol.3", [
        "カタルシスの月",
        "ムラサキグルマ",
    ])
    gpChallenge([hinabitter], [findChart("ロンロンへ　ライライライ！", 4)])

    limitedEvents = UnlockGroup.objects.get(name="Time-limited events")
    eventOrdering = UnlockEvent.objects.filter(group=limitedEvents).aggregate(Max('ordering'))['ordering__max']

    weather = UnlockEvent.objects.create(
       version_id=20,
       group=limitedEvents,
       name="GALAXY BRAVE: WEATHER",
       progressive=True,
       ordering=eventOrdering+10,
       amethyst_required=False, 
    )
    despair = UnlockEvent.objects.create(
        version_id=20,
        group=limitedEvents,
        name="GALAXY BRAVE: DESPAIR",
        progressive=True,
        ordering=eventOrdering+20,
        amethyst_required=False,
    )
    for diff in range(5):
        blizzard = findChart("Blizzard of Arrows", diff)
        btask = UnlockTask.objects.create(
            event=weather,
            name="Blizzard of Arrows ({})".format(Difficulty.objects.get(id=diff).name),
            ordering=diff*10,
        )
        ChartUnlock.objects.create(task=btask, chart=blizzard)

        meteor = findChart("Meteor", diff)
        mtask = UnlockTask.objects.create(
            event=despair,
            name="Meteor ({})".format(Difficulty.objects.get(id=diff).name),
            ordering=diff*10,
        )
        ChartUnlock.objects.create(task=mtask, chart=meteor)

    def rotate(goldTitle, silverTitle, bronzeTitle, defaultTitle):
        bronze = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="BRONZE CLASS").id
        silver = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="SILVER CLASS").id
        gold = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="GOLD CLASS").id
        advance = UnlockTask.objects.get(event__name="WORLD LEAGUE", name="GOLD CLASS with advanced border").id

        if goldTitle:
            goldUnlocks = ChartUnlock.objects.filter(task_id=advance, chart__song__title=goldTitle)
            for unlock in goldUnlocks:
                if unlock.chart.song.title == goldTitle:
                    unlock.task_id = gold
                    unlock.save()

        if silverTitle:
            silverUnlocks = ChartUnlock.objects.filter(task_id=gold, chart__song__title=silverTitle)
            for unlock in silverUnlocks:
                if unlock.chart.song.title == silverTitle:
                    unlock.task_id = silver
                    unlock.save()

        if bronzeTitle:
            bronzeUnlocks = ChartUnlock.objects.filter(task_id=silver, chart__song__title=bronzeTitle)
            for unlock in bronzeUnlocks:
                if unlock.chart.song.title == bronzeTitle:
                    unlock.task_id = bronze
                    unlock.save()

        if defaultTitle:
            defaultUnlocks = ChartUnlock.objects.filter(task_id=bronze, chart__song__title=defaultTitle)
            for unlock in defaultUnlocks:
                if unlock.chart.song.title == defaultTitle:
                    unlock.delete()

    rotate("STOMP!!", "Is this dance a Hakken?", None, None)

def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0176_20250201_content_catchup'),
    ]

    operations = [migrations.RunPython(forward, backward)]
