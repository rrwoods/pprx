from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	newChart = UnlockTask.objects.create(event=newChallengeChartsEvent, name="Glitch Angel Challenge", ordering=20)
	ChartUnlock.objects.create(version_id=18, task=newChart, chart=findChart("Glitch Angel", 4))

def backward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.filter(name="Glitch Angel Challenge").first().delete()


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0031_phlox')]
	operations = [migrations.RunPython(forward, backward)]