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
		return [c for c in candidates if (c.song.title == title)]

	def newGoldenLeague(new_title):
		advanceBorder = UnlockTask.objects.filter(name='GOLD CLASS with advanced border').first()
		for c in findCharts(new_title):
			ChartUnlock.objects.create(task=advanceBorder, chart=c)

		white = CabinetModel.objects.get(name="white")
		SongLock.objects.create(model=white, song=findSong(new_title))


	newGoldenLeague('9th Outburst')


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0125_gp_15_16_unlocked')]

	operations = [migrations.RunPython(forward, backward)]


