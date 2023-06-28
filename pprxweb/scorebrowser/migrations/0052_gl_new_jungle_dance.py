from django.db import migrations, models


def forward(apps, schema_editor):
	Song = apps.get_model("scorebrowser", "Song")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")
	SongLock = apps.get_model("scorebrowser", "SongLock")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

	def findSong(title):
		candidates = Song.objects.filter(title=title)
		for song in candidates:
			if song.title == title:
				return song

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title:
				return chart
		return None

	def newGoldenLeague(title, difficulty_ids):
		advanceBorder = UnlockTask.objects.filter(name='GOLD CLASS with advanced border').first()
		for d in difficulty_ids:
			ChartUnlock.objects.create(version_id=19, task=advanceBorder, chart=findChart(title, d))

		white = CabinetModel.objects.get(name="white")
		SongLock.objects.create(version_id=19, model=white, song=findSong(title))

	newGoldenLeague('Jungle Dance', [3])


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0051_gl_rotate_survival')]

	operations = [migrations.RunPython(forward, backward)]


