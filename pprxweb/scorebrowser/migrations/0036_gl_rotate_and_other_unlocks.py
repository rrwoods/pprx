from django.db import migrations, models

# I FORGOT TO ACTUALLY PUT GL ROTATION INTO THIS FILE.
# IT'S IN THE NEXT ONE.

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

	def createExtraSavior(version_id, event, title, difficulty_id, taskOrdering):
		difficulty = Difficulty.objects.filter(id=difficulty_id).first()
		chart = findChart(title, difficulty_id)
		task = UnlockTask.objects.create(event=event, name='{} ({} {})'.format(title, difficulty.name, chart.rating), ordering=taskOrdering)
		ChartUnlock.objects.create(version_id=version_id, task=task, chart=chart, extra=True)

	cherryBlossom = UnlockEvent.objects.create(name='[A3] 春を呼ぶ桜の祝祭', ordering=221)
	createExtraSavior(19, cherryBlossom, "chaplet", 3, 10)
	createExtraSavior(19, cherryBlossom, "spring pony", 3, 20)

	gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
	vol17 = UnlockTask.objects.create(event=gpAdvance, name="GRAND PRIX music pack vol.17", ordering=90)
	vol18 = UnlockTask.objects.create(event=gpAdvance, name="GRAND PRIX music pack vol.18", ordering=100)

	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("Hold Tight", 3))
	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("JUST BELIEVE", 3))
	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("LOVE SHINE (Body Grooverz 2006 mix)", 3))
	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("the beat", 3))

	ChartUnlock.objects.create(version_id=19, task=vol17, chart=findChart("Follow Tomorrow", 4))
	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("Follow Tomorrow", 4))
	ChartUnlock.objects.create(version_id=19, task=vol17, chart=findChart("Take A Step Forward", 4))
	ChartUnlock.objects.create(version_id=19, task=vol18, chart=findChart("Take A Step Forward", 4))	

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	newChallengeCharts = UnlockTask.objects.create(event=newChallengeChartsEvent, name="GP vols 17+18", ordering=20)
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("Follow Tomorrow", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("Take A Step Forward", 4))

def backward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")

	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.filter(name="GP vols 17+18").delete()
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.17").delete()
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.18").delete()
	UnlockEvent.objects.filter(name="[A3] 春を呼ぶ桜の祝祭").delete()


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0035_gold_is_gold')]

	operations = [migrations.RunPython(forward, backward)]