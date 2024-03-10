from django.db import migrations
from django.db.models import Max


def forward(apps, schema_editor):
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    SongLock = apps.get_model("scorebrowser", "SongLock")

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        return [c for c in candidates if (c.song.title == title)]

    def rotate(goldTitle, silverTitle, bronzeTitle, defaultTitle):
        bronze = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="BRONZE CLASS").first().id
        silver = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="SILVER CLASS").first().id
        gold = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="GOLD CLASS").first().id
        advance = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="GOLD CLASS with advanced border").first().id

        goldUnlocks = ChartUnlock.objects.filter(task_id=advance, chart__song__title=goldTitle)
        for unlock in goldUnlocks:
            if unlock.chart.song.title == goldTitle:
                unlock.task_id = gold
                unlock.save()

        silverUnlocks = ChartUnlock.objects.filter(task_id=gold, chart__song__title=silverTitle)
        for unlock in silverUnlocks:
            if unlock.chart.song.title == silverTitle:
                unlock.task_id = silver
                unlock.save()

        bronzeUnlocks = ChartUnlock.objects.filter(task_id=silver, chart__song__title=bronzeTitle)
        for unlock in bronzeUnlocks:
            if unlock.chart.song.title == bronzeTitle:
                unlock.task_id = bronze
                unlock.save()

        defaultUnlocks = ChartUnlock.objects.filter(task_id=bronze, chart__song__title=defaultTitle)
        for unlock in defaultUnlocks:
            if unlock.chart.song.title == defaultTitle:
                unlock.delete()

        SongLock.objects.filter(version_id=19, song__title=bronzeTitle).delete()

    rotate("Continue to the real world?", "GROOVE 04", "SURVIVAL AT THE END OF THE UNIVERSE", "TAKE ME HIGHER")



def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0126_gl_new_9th_outburst'),
    ]

    operations = [migrations.RunPython(forward, backward)]
