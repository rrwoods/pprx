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
		return chart

	kac = UnlockEvent.objects.filter(name='[A3] KONAMI Arcade Championship (2023) Entry Songs').first()
	kac1 = createExtraSavior(19, kac, "mathematical good-bye", 2, 12)
	kac2 = createExtraSavior(19, kac, "mathematical good-bye", 3, 13)
	kac3 = createExtraSavior(19, kac, "ROCK THE PARTY", 3, 16)

	entered = UnlockTask.objects.filter(name="Entered KAC 2023").first()
	ChartUnlock.objects.create(version_id=19, task=entered, chart=kac1)
	ChartUnlock.objects.create(version_id=19, task=entered, chart=kac2)
	ChartUnlock.objects.create(version_id=19, task=entered, chart=kac3)


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0076_muteki_buffalo_challenge')]

	operations = [migrations.RunPython(forward, backward)]