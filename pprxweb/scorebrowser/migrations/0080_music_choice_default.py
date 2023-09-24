from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UserUnlock = apps.get_model("scorebrowser", "UserUnlock")
	Difficulty = apps.get_model("scorebrowser", "Difficulty")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Chart = apps.get_model("scorebrowser", "Chart")
	
	# get the original acid tribal dance unlock task, and its event
	acidTribalTitle = "Acid,Tribal & Dance (DDR EDITION)"
	acidTribalTask = UnlockTask.objects.get(name=acidTribalTitle)
	musicChoice = acidTribalTask.event

	# create the extra savior tasks for acid tribal, in a new indentical-looking event
	musicChoiceExtraSavior = UnlockEvent.objects.create(name=musicChoice.name, ordering=musicChoice.ordering)
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
		return task
	acidTribalExpert    = createExtraSavior(19, musicChoiceExtraSavior, acidTribalTitle, 3, 100)
	acidTribalChallenge = createExtraSavior(19, musicChoiceExtraSavior, acidTribalTitle, 4, 100)

	# transfer all existing users' acid tribal unlocks to the new event
	for userUnlock in UserUnlock.objects.filter(task=acidTribalTask):
		user = userUnlock.user
		UserUnlock.objects.create(user=user, task=acidTribalExpert)
		UserUnlock.objects.create(user=user, task=acidTribalChallenge)

	# wipe the old event
	musicChoice.delete()


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0079_na_round1_default_region')]

	operations = [migrations.RunPython(forward, backward)]

