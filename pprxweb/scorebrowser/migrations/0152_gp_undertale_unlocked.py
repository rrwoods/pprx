from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="SPECIAL music pack feat.UNDERTALE").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0151_triple_tribe_2_extra_savior')]
	operations = [migrations.RunPython(forward, backward)]
