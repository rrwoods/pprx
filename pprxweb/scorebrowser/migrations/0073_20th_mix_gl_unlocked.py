from django.db import migrations, models
from django.db.models import Max

def forward(apps, schema_editor):
	SongLock = apps.get_model("scorebrowser", "SongLock")

	songs = [
		"BUTTERFLY (20th Anniversary Mix)",
		"CARTOON HEROES (20th Anniversary Mix)",
		"HAVE YOU NEVER BEEN MELLOW (20th Anniversary Mix)",
		"LONG TRAIN RUNNIN' (20th Anniversary Mix)",
		"SKY HIGH (20th Anniversary Mix)",
		"Lose Your Sense",
		"Sector",
		"Ability",
		"SURVIVAL AT THE END OF THE UNIVERSE",
		"Jungle Dance",
		"Rave in the Shell",
	]

	for title in songs:
		SongLock.objects.filter(song__title=title).delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0072_course_trials_20th_mix_challenge')]

	operations = [migrations.RunPython(forward, backward)]
