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

	courseTrialA3 = UnlockEvent.objects.filter(name="[A3] COURSE TRIAL A3").first()
	task = UnlockTask.objects.create(event=courseTrialA3, name="DISTORTION (unlocks アドレナリン)", ordering=80)
	ChartUnlock.objects.create(version_id=19, task=task, chart=findChart("アドレナリン", 3))

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0041_auto_20230410_1450')]

	operations = [migrations.RunPython(forward, backward)]