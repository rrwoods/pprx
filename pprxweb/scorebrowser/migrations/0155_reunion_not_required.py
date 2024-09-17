# Generated by Django 4.2.7 on 2024-09-15 17:05

from django.db import migrations

def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

    event = UnlockEvent.objects.get(name="MYSTICAL Re:UNION")
    event.amethyst_required = False
    event.save()


def backward(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0154_mystical_reunion'),
    ]

    operations = [
    ]