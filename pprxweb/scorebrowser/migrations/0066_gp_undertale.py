
from django.db import migrations, models
from django.db.models import Max

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")
	Difficulty = apps.get_model("scorebrowser", "Difficulty")

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
	# songs = {songName: [difficultyIds]} -- do NOT include challenge if a second pack is required to unlock it.
	def gpPack(packName, songs):
		gpPack.nextOrdering += 10
		pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=gpPack.nextOrdering)

		for title, difficulty_ids in songs.items():
			for difficulty_id in difficulty_ids:
				chart = findChart(title, difficulty_id)
				ChartUnlock.objects.create(version_id=19, task=pack, chart=chart)

		return pack
	gpPack.nextOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	def newChallengeChart(title):
		newChart = UnlockTask.objects.create(event=newChallengeChartsEvent, name="{} Challenge".format(title), ordering=20)
		chart = findChart(title, 4)
		ChartUnlock.objects.create(version_id=18, task=newChart, chart=chart)
		return chart

	def gpChallenge(packs, titles):
		charts = [newChallengeChart(title) for title in titles]
		for pack in packs:
			for chart in charts:
				ChartUnlock.objects.create(version_id=19, task=pack, chart=chart)


	undertale = gpPack("SPECIAL music pack feat.UNDERTALE", {})
	gpChallenge([undertale], [
		'Death by Glamour',
		'Finale',
		'Battle Against a True Hero',
	])

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0065_gl_rotate_jungle_dance_and_rave_in_the_shell')]
	operations = [migrations.RunPython(forward, backward)]
