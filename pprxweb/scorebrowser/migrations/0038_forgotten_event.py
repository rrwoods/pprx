from django.db import migrations, models


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
		return task   # used for events where you get a bonus song for unlocking everything

	event = UnlockEvent.objects.create(name="[A20 PLUS] いちかのBEMANI超じゃんけん大会2020", ordering=105)
	createExtraSavior(18, event, "星屑の夜果て", 3, 10)
	createExtraSavior(18, event, "び", 3, 30)
	createExtraSavior(18, event, "ラブキラ☆スプラッシュ", 3, 20)
	createExtraSavior(18, event, "Silly Love", 3, 40)


def backward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

	UnlockEvent.objects.filter(name="[A20 PLUS] いちかのBEMANI超じゃんけん大会2020").delete()


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0037_gl_rotate_for_real')]

	operations = [migrations.RunPython(forward, backward)]