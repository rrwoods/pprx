# Generated by Django 4.2.7 on 2024-11-09 02:09

from django.db import migrations
from django.db.models import Max

def forward(apps, schema_editor):
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")

    def findCharts(title):
        candidates = Chart.objects.filter(song__title=title)
        if len(candidates) == 0:
            raise Exception("No charts found for {}".format(title))
        return [c for c in candidates if (c.song.title == title)]

    worldLeague = UnlockEvent.objects.get(name="WORLD LEAGUE")
    goldClass = UnlockTask.objects.get(name="GOLD CLASS", event=worldLeague)
    for chart in findCharts("Is this dance a Hakken?"):
        ChartUnlock.objects.create(task=goldClass, chart=chart)


def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0171_gp_touhou_3_4_unlocked'),
    ]


    operations = [migrations.RunPython(forward, backward)]