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

	def rotate(goldTitle, silverTitle, bronzeTitle, defaultTitle):
		bronze = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="BRONZE CLASS").first().id
		silver = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="SILVER CLASS").first().id
		gold = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="GOLD CLASS").first().id
		advance = UnlockTask.objects.filter(event__name="GOLDEN LEAGUE A3", name="GOLD CLASS with advanced border").first().id

		goldUnlocks = ChartUnlock.objects.filter(task_id=advance, chart__song__title=goldTitle)
		for unlock in goldUnlocks:
			if unlock.chart.song.title == goldTitle:
				unlock.task_id = gold
				unlock.save()

		silverUnlocks = ChartUnlock.objects.filter(task_id=gold, chart__song__title=silverTitle)
		for unlock in silverUnlocks:
			if unlock.chart.song.title == silverTitle:
				unlock.task_id = silver
				unlock.save()

		bronzeUnlocks = ChartUnlock.objects.filter(task_id=silver, chart__song__title=bronzeTitle)
		for unlock in bronzeUnlocks:
			if unlock.chart.song.title == bronzeTitle:
				unlock.task_id = bronze
				unlock.save()

		defaultUnlocks = ChartUnlock.objects.filter(task_id=bronze, chart__song__title=defaultTitle)
		for unlock in defaultUnlocks:
			if unlock.chart.song.title == defaultTitle:
				unlock.delete()

	rotate("Sector", "TAKE ME HIGHER", "Environ [De-SYNC] (feat. lythe)", "DDR TAGMIX -LAST DanceR-")

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0036_gl_rotate_and_other_unlocks')]

	operations = [migrations.RunPython(forward, backward)]