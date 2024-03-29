# Generated by Django 3.2.16 on 2023-11-18 06:37

from django.db import migrations


def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

    musicChoice = UnlockEvent.objects.get(name="[A3] DANCE aROUND × DanceDanceRevolution 2022 natsu no MUSIC CHOICE")
    musicChoice.amethyst_required = True
    musicChoice.save()


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0102_user_selected_rank'),
    ]

    operations = [migrations.RunPython(forward, backward)]
