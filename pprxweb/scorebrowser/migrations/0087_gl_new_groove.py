from django.db import migrations, models


def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")
	Song = apps.get_model("scorebrowser", "Song")
	SongLock = apps.get_model("scorebrowser", "SongLock")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

	def findSong(title):
		candidates = Song.objects.filter(title=title)
		for song in candidates:
			if song.title == title:
				return song

	def findCharts(title):
		candidates = Chart.objects.filter(song__title=title)
		return [c for c in candidates if (c.song.title == title) and c.tracked]

	def newGoldenLeague(title):
		advanceBorder = UnlockTask.objects.filter(name='GOLD CLASS with advanced border').first()
		for c in findCharts(title):
			ChartUnlock.objects.create(version_id=19, task=advanceBorder, chart=c)

		white = CabinetModel.objects.get(name="white")
		SongLock.objects.create(model=white, song=findSong(title))


	newGoldenLeague('GROOVE 04')


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0086_relock_gls')]

	operations = [migrations.RunPython(forward, backward)]


