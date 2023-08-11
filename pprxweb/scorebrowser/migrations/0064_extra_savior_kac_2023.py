from django.db import migrations, models

# I FORGOT TO ACTUALLY PUT GL ROTATION INTO THIS FILE.
# IT'S IN THE NEXT ONE.

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

	kac = UnlockEvent.objects.create(name='[A3] KONAMI Arcade Championship (2023) Entry Songs', ordering=222)
	createExtraSavior(19, kac, "パーフェクトイーター", 3, 0) # not actually extra savior but its the easiest way.
	createExtraSavior(19, kac, "I-W-U (I Want U)", 3, 10)
	createExtraSavior(19, kac, "Sparkle Dreams", 3, 20)


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0063_draw_the_savage_challenge')]

	operations = [migrations.RunPython(forward, backward)]