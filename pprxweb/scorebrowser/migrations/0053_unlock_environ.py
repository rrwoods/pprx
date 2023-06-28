# forgot to allow environ on white cabs during its GL rotation.

from django.db import migrations, models

def forward(apps, schema_editor):
	SongLock = apps.get_model("scorebrowser", "SongLock")
	SongLock.objects.filter(version_id=19, song__title="Environ [De-SYNC] (feat. lythe)").delete()

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0052_gl_new_jungle_dance')]

	operations = [migrations.RunPython(forward, backward)]