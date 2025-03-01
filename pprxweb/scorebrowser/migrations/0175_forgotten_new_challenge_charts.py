# Generated by Django 4.2.7 on 2025-02-02 00:06

from django.db import migrations


def forward(apps, schema_editor):
    Chart = apps.get_model("scorebrowser", "Chart")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")


    def findChart(title, difficulty_id):
        candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
        for chart in candidates:
            if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
                return chart
        return None

    newChallengeChartsTask = UnlockTask.objects.get(name="New Challenge charts (A3+)")
    def newChallengeChart(title):
        ChartUnlock.objects.create(task=newChallengeChartsTask, chart=findChart(title, 4))

    ### HOPEFULLY this is the last time I need to do this, because
    ### the chart updater will do this for me automatically from now on.
    newChallengeChart("BE LOVIN")
    newChallengeChart("Holic")
    newChallengeChart("華爛漫 -Flowers-")
    newChallengeChart("PARANOIA EVOLUTION")
    newChallengeChart("Übertreffen")
    newChallengeChart("Come Back To Me")


def backward(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0174_one_task_for_new_challenge'),
    ]

    operations = [migrations.RunPython(forward, backward)]
