from django.db import migrations, models


def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title:
				return chart
		return None

	advanceBorder = UnlockTask.objects.filter(name='GOLD CLASS with advanced border').first()
	ChartUnlock.objects.create(version_id=19, task=advanceBorder, chart=findChart('Ability', 3))


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0038_forgotten_event')]

	operations = [migrations.RunPython(forward, backward)]