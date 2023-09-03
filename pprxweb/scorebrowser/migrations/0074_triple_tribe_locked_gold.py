from django.db import migrations, models

def forward(apps, schema_editor):
	SongLock = apps.get_model("scorebrowser", "SongLock")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

	white = CabinetModel.objects.get(name="white")
	for title in ['C-C-C-N-N-N', 'DIABLOSIS::Nāga', 'suspicions']:
		lock = SongLock.objects.filter(song__title=title).first()
		lock.model = white
		lock.save()


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0073_20th_mix_gl_unlocked')]

	operations = [migrations.RunPython(forward, backward)]