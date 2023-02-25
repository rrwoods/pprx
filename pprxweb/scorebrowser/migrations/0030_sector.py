from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	advanceBorder = UnlockTask.objects.filter(name='GOLD CLASS with advanced border').first()
	ChartUnlock.objects.create(version_id=19, task=advanceBorder, chart=findChart('Sector', 3))

	goldClass = UnlockTask.objects.filter(name='GOLD CLASS (or SILVER with advanced border)').first()
	if goldClass:
		goldClass.name = 'GOLD CLASS'
		goldClass.save()


def backward(apps, schema_editor):
	Chart = apps.get_model("scorebrowser", "Chart")
	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	ChartUnlock.objects.filter(chart=findChart('Sector', 3)).delete()


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0029_take_me_higher')]

	operations = [migrations.RunPython(forward, backward)]