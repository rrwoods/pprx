from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		return Chart.objects.filter(song__title=title, difficulty_id=difficulty_id).first()

	def rotateExtraExclusive(departing, arriving, difficulty_ids):
		extraExclusive = UnlockTask.objects.filter(name="EXTRA EXCLUSIVE").first()
		ChartUnlock.objects.filter(task=extraExclusive, chart__song__title=departing).delete()
		for difficulty_id in difficulty_ids:
			ChartUnlock.objects.create(version_id=19, task=extraExclusive, chart=findChart(arriving, difficulty_id), extra=True)

	rotateExtraExclusive('THE ANCIENT KING IS BACK', 'Pure Rude', [3])

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0059_bpls2_vols_1_to_8')]

	operations = [migrations.RunPython(forward, backward)]