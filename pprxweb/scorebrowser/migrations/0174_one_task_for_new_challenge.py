# Generated by Django 4.2.7 on 2025-01-30 20:20

from django.db import migrations


def forward(apps, schema_editor):
    UnlockGroup = apps.get_model("scorebrowser", "UnlockGroup")
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
    ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
    Chart = apps.get_model("scorebrowser", "Chart")


    event = UnlockEvent.objects.get(name="New Challenge charts (A3)")

    tasks = list(UnlockTask.objects.filter(event=event))

    unlocks = []
    for task in tasks:
        for unlock in ChartUnlock.objects.filter(task=task):
            unlocks.append(unlock)

    singleTask = UnlockTask.objects.create(event=event, name="New Challenge charts (A3+)", ordering=0)

    for unlock in unlocks:
        unlock.task = singleTask
        unlock.save()

    for task in tasks:
        task.delete()


def backward(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0173_gl_new_hyper_focus_and_1st_classic_challenge'),
    ]

    operations = [migrations.RunPython(forward, backward)]
