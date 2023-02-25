from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent") 
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		return Chart.objects.filter(song__title=title, difficulty_id=difficulty_id).first()

	loseYourSense = ChartUnlock.objects.filter(chart__song__title="Lose Your Sense").first()
	goldClass = UnlockTask.objects.filter(name='GOLD CLASS (or SILVER with advanced border)', event__name="GOLDEN LEAGUE A3").first()
	loseYourSense.task = goldClass
	loseYourSense.save()

	gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
	vol15 = UnlockTask.objects.create(event=gpAdvance, name="GRAND PRIX music pack vol.15", ordering=70)
	vol16 = UnlockTask.objects.create(event=gpAdvance, name="GRAND PRIX music pack vol.16", ordering=80)
	ChartUnlock.objects.create(version_id=19, task=vol15, chart=findChart("ALGORITHM", 4))
	ChartUnlock.objects.create(version_id=19, task=vol16, chart=findChart("ALGORITHM", 4))
	ChartUnlock.objects.create(version_id=19, task=vol15, chart=findChart("Blue Rain", 4))
	ChartUnlock.objects.create(version_id=19, task=vol16, chart=findChart("Blue Rain", 4))

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	newChallengeCharts = UnlockTask.objects.create(event=newChallengeChartsEvent, name="GP vols 15+16", ordering=20)
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("ALGORITHM", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("Blue Rain", 4))

def backward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.filter(name="GP vols 15+16").delete()
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.15").delete()
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.16").delete()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0027_clearer_course_unlocks')]

	operations = [migrations.RunPython(forward, backward)]