from django.db import migrations, models

def forward(apps, schema_editor):
	SongLock = apps.get_model("scorebrowser", "SongLock")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")
	Song = apps.get_model("scorebrowser", "Song")

	white = CabinetModel.objects.get(name="white")
	for title in ['コメット⇒スケイター', '3y3s', 'Ambivalent Vermilia']:
		song = Song.objects.get(title=title)
		SongLock.objects.create(model=white, song=song)


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0142_userscore_quality')]

	operations = [migrations.RunPython(forward, backward)]