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

	def songUnlock(version_id, event, taskName, title, difficulty_ids, taskOrdering):
		task = UnlockTask.objects.create(event=event, name=taskName, ordering=taskOrdering)
		for difficulty_id in difficulty_ids:
			chart = findChart(title, difficulty_id)
			ChartUnlock.objects.create(version_id=version_id, task=task, chart=chart)

	kac = UnlockEvent.objects.filter(ordering=222).first()
	kac.ordering = 250
	kac.save()

	tripleTribe = UnlockEvent.objects.create(name='[A3] BEMANI PRO LEAGUE -SEASON 3- Triple Tribe', ordering=260)
	songUnlock(19, tripleTribe, '700 TB (C-C-C-N-N-N)', 'C-C-C-N-N-N', [3], 0)
	songUnlock(19, tripleTribe, '1400 TS (DIABLOSIS::Nāga)', 'DIABLOSIS::Nāga', [2, 3], 10)
	songUnlock(19, tripleTribe, '2100 each (suspicions)', 'suspicions', [2, 3], 10)


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0067_kac_corrections')]

	operations = [migrations.RunPython(forward, backward)]