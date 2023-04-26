
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

	# taskName = the name of the music pack
	# songs = {songName: [difficultyIds]}
	def pairOfGpPacks(taskName1, songs1, taskName2, songs2):
		gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
		lastOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']
		pack1 = UnlockTask.objects.create(event=gpAdvance, name=taskName1, ordering=lastOrdering+10)
		pack2 = UnlockTask.objects.create(event=gpAdvance, name=taskName2, ordering=lastOrdering+20)

		challenge1 = []
		for title, difficulty_ids in songs1.items():
			for difficulty_id in difficulty_ids:
				chart = findChart(title, difficulty_id)
				ChartUnlock.objects.create(version_id=19, task=pack1, chart=chart)
				if difficulty_id == 4:
					challenge1.append(chart)
		for chart in challenge1:
			ChartUnlock.objects.create(version_id=19, task=pack2, chart=chart)

		challenge2 = []
		for title, difficulty_ids in songs2.items():
			for difficulty_id in difficulty_ids:
				chart = findChart(title, difficulty_id)
				ChartUnlock.objects.create(version_id=19, task=pack2, chart=chart)
				if difficulty_id == 4:
					challenge2.append(chart)
		for chart in challenge2:
			ChartUnlock.objects.create(version_id=19, task=pack1, chart=chart)

	songs1 = {
		"Flip Flap": [3],
		"GLITTER": [3],
		"Valanga": [3, 4],
		"カラフルミニッツ": [3]
	}
	songs2 = {
		"Broken": [3],
		"Playing With Fire": [3],
		"Towards The Horizon": [3],
		"伐折羅-vajra-": [3, 4],
	}
	pairOfGpPacks("SPECIAL music pack feat.REFLEC BEAT vol.1", songs1, "SPECIAL music pack feat.REFLEC BEAT vol.2", songs2)

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0043_golden_arrow_challenge')]
	operations = [migrations.RunPython(forward, backward)]
