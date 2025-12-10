from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")
    UserUnlock = apps.get_model("scorebrowser", "UserUnlock")
    SongLock = apps.get_model("scorebrowser", "SongLock")

    timeLimited = UnlockGroup.objects.get(name="Time-limited events")
    extraSavior = UnlockGroup.objects.get(name="Extra Savior")

    tripleTribe = UnlockEvent.objects.get(name="BEMANI PRO LEAGUE -SEASON 4- Triple Tribe")
    tokio, soflan, cosmic = UnlockTask.objects.filter(event=tripleTribe).order_by('ordering')
    tokioUnlocks = UserUnlock.objects.filter(task=tokio)
    soflanUnlocks = UserUnlock.objects.filter(task=soflan)
    cosmicUnlocks = UserUnlock.objects.filter(task=cosmic)

    ordering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max']
    tripleTribeEs = UnlockEvent.objects.create(version_id=20, group=extraSavior, name="BEMANI PRO LEAGUE -SEASON 4- Triple Tribe", ordering=ordering+10)

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).order_by('difficulty_id')
        if len(candidates) == 0:
            raise Exception("No charts for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def transferExtraSaviors(event, title, unlocks):
        for chart in findCharts(title):
            task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=transferExtraSaviors.esTaskOrdering)
            unlock = ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            if chart.difficulty_id != 4:
                transferExtraSaviors.esUnlockGrants += [UserUnlock(user=oldUnlock.user, task=task) for oldUnlock in unlocks]
            transferExtraSaviors.esTaskOrdering += 10
    transferExtraSaviors.esTaskOrdering = 0
    transferExtraSaviors.esUnlockGrants = []

    transferExtraSaviors(tripleTribeEs, 'ハイテックトキオ', tokioUnlocks)
    transferExtraSaviors(tripleTribeEs, '混乱少女♥そふらんちゃん!!', soflanUnlocks)
    transferExtraSaviors(tripleTribeEs, 'COSMIC V3LOCITY', cosmicUnlocks)
    UserUnlock.objects.bulk_create(transferExtraSaviors.esUnlockGrants)

    tripleTribe.delete()

def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0198_put_back_sahara_1116_unlocks'),
    ]

    operations = [migrations.RunPython(forward, backward)]
