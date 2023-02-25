from django.db import migrations, models

def forward(apps, schema_editor):
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")

	def findChart(title, difficulty_id):
		candidates = Chart.objects.filter(song__title=title, difficulty_id=difficulty_id)
		for chart in candidates:
			if chart.song.title == title: # 'take me higher' / 'TAKE ME HIGHER' sql collation woes
				return chart
		return None

	takeMeHigher = ChartUnlock.objects.filter(chart__song__title='take me higher', task__name='GOLD CLASS (or SILVER with advanced border)').first()
	if takeMeHigher:  # this didn't happen locally.
		TAKEMEHIGHER = findChart('TAKE ME HIGHER', 3)
		takeMeHigher.chart = TAKEMEHIGHER
		takeMeHigher.save()


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0028_unlock_updates_2023_02_20')]

	operations = [migrations.RunPython(forward, backward)]