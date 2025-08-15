from django.db import migrations
from django.db.models import Max



def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    Difficulty = apps.get_model("scorebrowser", "Difficulty")


    UnlockTask.objects.get(name="music pack vol.27").delete()
    UnlockTask.objects.get(name="music pack vol.28").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.DANCERUSH STARDOM vol.1").delete()
    UnlockTask.objects.get(name="SPECIAL music pack feat.DANCERUSH STARDOM vol.2").delete()

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

    chart1 = gpPack("chart pack vol.2", [])
    gpChallenge([chart1], [
        findChart("321STARS", 4),
        findChart("AA", 4),
        findChart("AM-3P", 4),
        findChart("BABY BABY GIMME YOUR LOVE", 4),
        findChart("DROP OUT", 4),
        findChart("exotic ethnic", 4),
        findChart("MAKE IT BETTER", 4),
        findChart("Silent Hill", 4),
        findChart("Silver Platform - I wanna get your heart -", 4),
        findChart("男々道", 4),
    ])


    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def songUnlock(event, taskName, title, taskOrdering):
        task = UnlockTask.objects.create(event=event, name=taskName, ordering=taskOrdering)
        for chart in findCharts(title):
            ChartUnlock.objects.create(task=task, chart=chart)

    limited = UnlockGroup.objects.get(name="Time-limited events")
    lastEventOrdering = UnlockEvent.objects.filter(group=limited).aggregate(Max('ordering'))['ordering__max']
    tripleTribe = UnlockEvent.objects.create(
        version_id=20,
        group=limited,
        name='BEMANI PRO LEAGUE -SEASON 5- Triple Tribe 0',
        ordering=lastEventOrdering+10,
        amethyst_required=False,
    )
    songUnlock(tripleTribe, '800 TB (ZENDEGI DANCE)', 'ZENDEGI DANCE', 0)
    songUnlock(tripleTribe, '2000 TB (疾風迅雷)', '疾風迅雷', 10)
    songUnlock(tripleTribe, '400 TS (Bye or not)', 'Bye or not', 20)
    songUnlock(tripleTribe, '1400 TS (Daisycutter)', 'Daisycutter', 30)
    songUnlock(tripleTribe, '2700 each (EYE OF THE HEAVEN)', 'EYE OF THE HEAVEN', 40)


    brave = UnlockEvent.objects.create(
       version_id=20,
       group=limited,
       name="GALAXY BRAVE: VOLTAGE",
       progressive=True,
       ordering=lastEventOrdering+20,
       amethyst_required=False, 
    )
    for diff in range(5):
        chart = findChart("Saiph", diff)
        task = UnlockTask.objects.create(
            event=brave,
            name="Saiph ({})".format(Difficulty.objects.get(id=diff).name),
            ordering=diff*10,
        )
        ChartUnlock.objects.create(task=task, chart=chart)



def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0191_ask_only_private'),
    ]

    operations = [migrations.RunPython(forward, backward)]
