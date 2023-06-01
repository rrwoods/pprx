
from django.db import migrations, models
from django.db.models import Max

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

	gpAdvance = UnlockEvent.objects.filter(name='GRAND PRIX Advance Play').first()
	# songs = {songName: [difficultyIds]} -- do NOT include challenge if a second pack is required to unlock it.
	def gpPack(packName, songs):
		gpPack.nextOrdering += 10
		pack = UnlockTask.objects.create(event=gpAdvance, name=packName, ordering=gpPack.nextOrdering)

		for title, difficulty_ids in songs.items():
			for difficulty_id in difficulty_ids:
				chart = findChart(title, difficulty_id)
				ChartUnlock.objects.create(version_id=19, task=pack, chart=chart)

		return pack
	gpPack.nextOrdering = UnlockTask.objects.filter(event=gpAdvance).aggregate(Max('ordering'))['ordering__max']

	def gpChallenge(packs, titles):
		# THIS FUNCTION IS MISSING THE LOGIC TO LOCK NEW CHARTS FOR OLD SONGS ON WHITE CAB.
		# SEE THE NEXT MIGRATION FOR THAT LOGIC, AND ADD IT HERE BEFORE REUSING.
		charts = [findChart(title, 4) for title in titles]
		for pack in packs:
			for chart in charts:
				ChartUnlock.objects.create(version_id=19, task=pack, chart=chart)

	vol19 = gpPack("GRAND PRIX music pack vol.19", {})
	vol20 = gpPack("GRAND PRIX music pack vol.20", {})
	gpChallenge([vol19, vol20], ["朧 (dj TAKA Remix)", "Programmed Universe"])

	songs22 = {
		"Open Your Eyes": [3],
		"Racing with Time (NAOKI's 999 remix)": [3],
		"SAY A PRAYER": [3],
		"Surrender (PureFocus remix)": [3],
	}
	vol21 = gpPack("GRAND PRIX music pack vol.21", {})
	vol22 = gpPack("GRAND PRIX music pack vol.22", songs22)
	gpChallenge([vol21, vol22], ["starmine", "UNBELIEVABLE (Sparky remix)"])

	songsBpl = {
		"BREAKING THE FUTURE": [2, 3]
	}
	gpPack("BPL S2 music pack vol.0", songsBpl)
	

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0048_cyberconnect_challenge')]
	operations = [migrations.RunPython(forward, backward)]
