from django.db import migrations


def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

    UnlockEvent.objects.filter(version_id=19, group__name="Extra Savior").delete()
    UnlockEvent.objects.filter(version_id=19, group__name="Course Trial").delete()
    UnlockEvent.objects.filter(version_id=19, group__name="Golden League").delete()
    UnlockEvent.objects.filter(name="BABY-LON'S GALAXY").delete()
    UnlockEvent.objects.filter(name="BABY-LON'S GALAXY ENCORE EXTRA STAGE").delete()

def backward(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0136_chart_rerate'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
