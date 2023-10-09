from django.db import migrations

def forward(apps, schema_editor):
    SongLock = apps.get_model("scorebrowser", "SongLock")
    CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

    white = CabinetModel.objects.get(name='white')
    wrongLocks = SongLock.objects.filter(model__name='gold')
    for lock in wrongLocks:
        lock.model = white
        lock.save()

def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0087_gl_new_groove'),
    ]

    operations = [
        migrations.RunPython(forward, backward)
    ]
