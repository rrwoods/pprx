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

    time_limited = UnlockGroup.objects.get(name="Time-limited events")
    extra_savior = UnlockGroup.objects.get(name="Extra Savior")

    triple_tribe = UnlockEvent.objects.get(name="BEMANI PRO LEAGUE -SEASON 3- Triple Tribe (Part 2)")
    comet = UnlockTask.objects.get(name="700 TB (コメット⇒スケイター)", event=triple_tribe)
    eyes = UnlockTask.objects.get(name="1400 TS (3y3s)", event=triple_tribe)
    ambi = UnlockTask.objects.get(name="2100 each (Ambivalent Vermilia)", event=triple_tribe)

    comet_unlocks = UserUnlock.objects.filter(task=comet)
    eyes_unlocks = UserUnlock.objects.filter(task=eyes)
    ambi_unlocks = UserUnlock.objects.filter(task=ambi)

    ordering = UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max']
    triple_tribe_es = UnlockEvent.objects.create(version_id=20, group=extra_savior, name="BEMANI PRO LEAGUE -SEASON 3- Triple Tribe", ordering=ordering+10)

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title).order_by('difficulty_id')
        if len(candidates) == 0:
            raise Exception("No charts for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    def transfer_extra_saviors(event, title, unlocks):
        for chart in findCharts(title):
            task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating), ordering=transfer_extra_saviors.task_ordering)
            unlock = ChartUnlock.objects.create(task=task, chart=chart, extra=True)
            if chart.difficulty_id != 4:
                transfer_extra_saviors.grant_unlocks += [UserUnlock(user=old_unlock.user, task=task) for old_unlock in unlocks]
            transfer_extra_saviors.task_ordering += 10
        SongLock.objects.get(song__title=title).delete()
    transfer_extra_saviors.task_ordering = 0
    transfer_extra_saviors.grant_unlocks = []

    transfer_extra_saviors(triple_tribe_es, 'コメット⇒スケイター', comet_unlocks)
    transfer_extra_saviors(triple_tribe_es, '3y3s', eyes_unlocks)
    transfer_extra_saviors(triple_tribe_es, 'Ambivalent Vermilia', ambi_unlocks)
    UserUnlock.objects.bulk_create(transfer_extra_saviors.grant_unlocks)

    triple_tribe.delete()


def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0177_20250222_content'),
    ]

    operations = [migrations.RunPython(forward, backward)]
