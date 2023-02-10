from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	ChartUnlock = apps.get_model("scorebrowser", "ChartUnlock")
	Song = apps.get_model("scorebrowser", "Song")
	Chart = apps.get_model("scorebrowser", "Chart")
	Difficulty = apps.get_model("scorebrowser", "Difficulty")

	def findChart(title, difficulty_id):
		return Chart.objects.filter(song__title=title, difficulty_id=difficulty_id).first()

	newChallengeChartsEvent = UnlockEvent.objects.filter(name="New Challenge charts (A3)").first()
	newChallengeCharts = UnlockTask.objects.create(event=newChallengeChartsEvent, name="Challenge charts I forgot before", ordering=10)
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("HAPPY☆ANGEL", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("ZETA～素数の世界と超越者～", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("Starlight in the Snow", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("CRAZY♥LOVE", 4))
	ChartUnlock.objects.create(version_id=18, task=newChallengeCharts, chart=findChart("Wow Wow VENUS", 4))

	bagChallengeSucksEvent = UnlockEvent.objects.create(name="bag Challenge should not exist", ordering=-100)
	bagChallengeSucksTask = UnlockTask.objects.create(event=bagChallengeSucksEvent, name="check this box to unhide bag Challenge (but why tho)", ordering=10)
	ChartUnlock.objects.create(version_id=18, task=bagChallengeSucksTask, chart=findChart("bag", 4))
	ChartUnlock.objects.create(version_id=19, task=bagChallengeSucksTask, chart=findChart("bag", 4))

def backward(apps, schema_editor):
	UnlockTask.objects.filter(name="Challenge charts I forgot before").delete()
	UnlockEvent.objects.filter(name="bag Challenge should not exist").delete()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0021_cabinet_data_the_right_way')]

	operations = [migrations.RunPython(forward, backward)]