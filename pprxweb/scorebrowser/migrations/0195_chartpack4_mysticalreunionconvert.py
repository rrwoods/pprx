from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UserUnlock = apps.get_model("scorebrowser", "UserUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    Difficulty = apps.get_model("scorebrowser", "Difficulty")


    UnlockTask.objects.get(name="BEMANI SELECTION music pack vol.2").delete()
    UnlockTask.objects.get(name="music pack vol.31").delete()
    UnlockTask.objects.get(name="music pack vol.32").delete()


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

    chart4 = gpPack("chart pack vol.4", [])
    gpChallenge([chart4], [
        findChart("AFTER THE GAME OF LOVE", 4),
        findChart("BRE∀K DOWN！", 4),
        findChart("CANDY☆", 4),
        findChart("e-motion", 4),
        findChart("Healing Vision ～Angelic mix～", 4),
        findChart("HYSTERIA", 4),
        findChart("Tomorrow Perfume", 4),
        findChart("xenon", 4),
        findChart("蒼い衝動 ～for EXTREME～", 4),
        findChart("月光蝶", 4),
    ])

    # def createExtraSaviors(event, title):
    #     for chart in findCharts(title):
    #         task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=createExtraSaviors.nextOrdering)
    #         ChartUnlock.objects.create(task=task, chart=chart, extra=True)
    #         createExtraSaviors.nextOrdering += 10
    # createExtraSaviors.nextOrdering = 0
    mystical = UnlockEvent.objects.get(name="MYSTICAL Re:UNION")

    extra_savior = UnlockGroup.objects.get(name="Extra Savior")

    concerto = UnlockTask.objects.get(name="250 BRS & BRD (Blφφdy Cφncertφ)")
    strike = UnlockTask.objects.get(name="600 BRS & BRD (OROCHI STRIKE)")
    lichtsaule = UnlockTask.objects.get(name="1500 BRS & BRD (Lichtsäule)")
    reincarnation = UnlockTask.objects.get(name="3750 BRS & BRD (REINCARNATION)")
    rerhyze = UnlockTask.objects.get(name="4000 BRS & BRD (Re:RHYZE)")

    concerto_unlocks = UserUnlock.objects.filter(task=concerto)
    strike_unlocks = UserUnlock.objects.filter(task=strike)
    lichtsaule_unlocks = UserUnlock.objects.filter(task=lichtsaule)
    reincarnation_unlocks = UserUnlock.objects.filter(task=reincarnation)
    rerhyze_unlocks = UserUnlock.objects.filter(task=rerhyze)

    ordering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max']
    mystical_es = UnlockEvent.objects.create(
        version_id=20,
        group=extra_savior,
        name="MYSTICAL Re:UNION",
        ordering=ordering+10,
    )

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).order_by("difficulty_id")
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def transfer_extra_saviors(event, title, unlocks):
        for chart in findCharts(title):
            task = UnlockTask.objects.create(
                event=event, 
                name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), 
                ordering=transfer_extra_saviors.task_ordering,
            )
            unlock = ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            if chart.difficulty_id != 4:
                transfer_extra_saviors.grant_unlocks += [UserUnlock(user=old_unlock.user, task=task) for old_unlock in unlocks]
            transfer_extra_saviors.task_ordering += 10
    transfer_extra_saviors.task_ordering = 0
    transfer_extra_saviors.grant_unlocks = []

    transfer_extra_saviors(mystical_es, 'Blφφdy Cφncertφ', concerto_unlocks)
    transfer_extra_saviors(mystical_es, 'OROCHI STRIKE', strike_unlocks)
    transfer_extra_saviors(mystical_es, 'Lichtsäule', lichtsaule_unlocks)
    transfer_extra_saviors(mystical_es, 'REINCARNATION', reincarnation_unlocks)
    transfer_extra_saviors(mystical_es, 'Re:RHYZE', rerhyze_unlocks)

    mystical.delete()


def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0194_chartpack3_3rdaudition_brainheart'),
    ]

    operations = [migrations.RunPython(forward, backward)]
