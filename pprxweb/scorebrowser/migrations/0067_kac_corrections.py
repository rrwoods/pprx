from django.db import migrations, models

def forward(apps, schema_editor):
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	# its wrong to have made the base song extra savior as a shortcut, because it shows up as available on extra stage.
	kacUnlock = ChartUnlock.objects.filter(chart__song__title='パーフェクトイーター').first()
	kacUnlock.task.name = "Entered KAC 2023"
	kacUnlock.task.save()
	kacUnlock.extra = False
	kacUnlock.save()

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	# the base unlock task is required to be completed to even see the other two songs in extra.
	ChartUnlock.objects.create(version_id=19, task=kacUnlock.task, chart=findChart("I-W-U (I Want U)", 3))
	ChartUnlock.objects.create(version_id=19, task=kacUnlock.task, chart=findChart("Sparkle Dreams", 3))

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0066_gp_undertale')]
	operations = [migrations.RunPython(forward, backward)]
