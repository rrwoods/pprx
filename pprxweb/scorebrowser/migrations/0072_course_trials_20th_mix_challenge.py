from django.db import migrations, models
from django.db.models import Max

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

	# THIS COURSE TRIAL FUNCTION IS DIFFERENT
	# DO NOT COPY IT FOR A NORMAL COURSE TRIAL!
	def courseTrial(course_name, title):
		courseTrialA3 = UnlockEvent.objects.filter(name="[A3] COURSE TRIAL A3").first()
		lastOrdering = UnlockTask.objects.filter(event=courseTrialA3).aggregate(Max('ordering'))['ordering__max']

		task = UnlockTask.objects.create(event=courseTrialA3, name="{} (unlocks {} challenge)".format(course_name, title), ordering=lastOrdering+10)
		ChartUnlock.objects.create(version_id=19, task=task, chart=findChart(title, 4))

	courseTrial("RELAXING", "HAVE YOU NEVER BEEN MELLOW (20th Anniversary Mix)")
	courseTrial("HEROES", "CARTOON HEROES (20th Anniversary Mix)")
	courseTrial("RUNNING", "LONG TRAIN RUNNIN' (20th Anniversary Mix)")
	courseTrial("SKYWARDS", "SKY HIGH (20th Anniversary Mix)")
	courseTrial("FLAPPING", "BUTTERFLY (20th Anniversary Mix)")

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0071_gp_new_not_alone')]

	operations = [migrations.RunPython(forward, backward)]
