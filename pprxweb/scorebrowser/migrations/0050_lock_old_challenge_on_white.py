from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		return Chart.objects.filter(song__title=title, difficulty_id=difficulty_id).first()

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	def newChallengeChart(title):
		newChart = UnlockTask.objects.create(event=newChallengeChartsEvent, name="{} Challenge".format(title), ordering=20)
		ChartUnlock.objects.create(version_id=18, task=newChart, chart=findChart(title, 4))

	newChallengeChart("朧 (dj TAKA Remix)")
	newChallengeChart("Programmed Universe")
	newChallengeChart("starmine")
	newChallengeChart("UNBELIEVABLE (Sparky remix)")

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0049_bpl_gp_drop')]

	operations = [migrations.RunPython(forward, backward)]