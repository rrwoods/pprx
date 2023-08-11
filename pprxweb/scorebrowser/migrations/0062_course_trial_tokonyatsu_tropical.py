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

	def courseTrial(course_name, title, difficulty_ids):
		courseTrialA3 = UnlockEvent.objects.filter(name="[A3] COURSE TRIAL A3").first()
		lastOrdering = UnlockTask.objects.filter(event=courseTrialA3).aggregate(Max('ordering'))['ordering__max']

		task = UnlockTask.objects.create(event=courseTrialA3, name="{} (unlocks {})".format(course_name, title), ordering=lastOrdering+10)
		for difficulty_id in difficulty_ids:
			ChartUnlock.objects.create(version_id=19, task=task, chart=findChart(title, difficulty_id))

	courseTrial("SUMMER RESORT", "とこにゃつ☆トロピカル", [3])

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0061_gl_new_rave_in_the_shell')]

	operations = [migrations.RunPython(forward, backward)]
