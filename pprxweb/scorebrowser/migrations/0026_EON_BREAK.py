from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		return Chart.objects.filter(song__title=title, difficulty_id=difficulty_id).first()

	extraExclusive = UnlockTask.objects.filter(name="EXTRA EXCLUSIVE").first()
	ChartUnlock.objects.filter(task=extraExclusive, chart__song__title="Deep tenDon Reflex").delete()
	ChartUnlock.objects.create(version_id=19, task=extraExclusive, chart=findChart("Eon Break", 3), extra=True)
	ChartUnlock.objects.create(version_id=19, task=extraExclusive, chart=findChart("Eon Break", 4), extra=True)

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0025_clearer_event_names')]

	operations = [migrations.RunPython(forward, backward)]