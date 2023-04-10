from django.db import migrations, models


def forward(apps, schema_editor):
	Song = apps.get_model("scorebrowser", "Song")
	SongLock = apps.get_model("scorebrowser", "SongLock")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

	def findSong(title):
		candidates = Song.objects.filter(title=title)
		for song in candidates:
			if song.title == title:
				return song

	SongLock.objects.filter(song__title="take me higher").delete()

	white = CabinetModel.objects.get(name="white")
	SongLock.objects.create(version_id=19, model=white, song=findSong("TAKE ME HIGHER"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Sector"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Ability"))

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0039_ability')]

	operations = [migrations.RunPython(forward, backward)]