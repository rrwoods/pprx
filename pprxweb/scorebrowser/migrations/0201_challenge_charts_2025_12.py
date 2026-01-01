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

    def gpChallenge(packs, titles):
        for pack in packs:
            for title in titles:
                chart = findChart(title, 4)
                ChartUnlock.objects.create(task=pack, chart=chart)    

    gpChallenge([gpPack("GRAND PRIX chart pack vol.5", [])], [
        "BROKEN MY HEART",
        "Dragon Blade",
        "D2R",
        "Funk Boogie",
        "Gamelan de Couple",
        "La Señorita",
        "No.13",
        "Quick Master",
        "WILD RUSH",
        "カゲロウ",
    ])

    gpChallenge([gpPack("GRAND PRIX chart pack vol.6", [])], [
        "AFRONOVA",
        "BURNING HEAT! (3 Option MIX)",
        "Can Be Real",
        "ECSTASY",
        "HIGHER",
        "INSIDE YOUR HEART",
        "LOGICAL DASH",
        "rainbow rainbow",
        "RED ZONE",
        "Unreal",
    ])

    gpChallenge([gpPack("BEMANI SELECTION music pack vol.4", [])], [
        "輪廻の鴉",
        "SURVIVAL AT THE END OF THE UNIVERSE",
        "Unreality",
    ])

    def createChallengeExtraSavior(event, title):
        chart = findChart(title, 4)
        task = UnlockTask.objects.create(event=event, name='{} (Challenge {})'.format(title, chart.rating), ordering=createChallengeExtraSavior.nextOrdering)
        ChartUnlock.objects.create(task=task, chart=chart, extra=True)
        createChallengeExtraSavior.nextOrdering += 10
    createChallengeExtraSavior.nextOrdering = 0

    extra_savior = UnlockGroup.objects.get(name="Extra Savior")
    eventOrdering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10
    hinabitter1 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st ひなビタ♪ CHALLENGE phase 1",
        ordering=eventOrdering,
    )
    hinabitter2 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st ひなビタ♪ CHALLENGE phase 2",
        ordering=eventOrdering+10,
    )
    hinabitter3 = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="The 1st ひなビタ♪ CHALLENGE phase 3",
        ordering=eventOrdering+20,
    )

    createChallengeExtraSavior(hinabitter1, "黒髪乱れし修羅となりて～凛 edition～")
    createChallengeExtraSavior(hinabitter1, "激アツ☆マジヤバ☆チアガール")
    createChallengeExtraSavior(hinabitter1, "ロマンシングエスケープ")
    createChallengeExtraSavior(hinabitter2, "地方創生☆チクワクティクス")
    createChallengeExtraSavior(hinabitter3, "漆黒のスペシャルプリンセスサンデー")

def backward(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0200_jubeat3_vol33_vol34_unlocked'),
    ]

    operations = [migrations.RunPython(forward, backward)]
