from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="SPECIAL music pack feat.jubeat vol.3").delete()
	UnlockTask.objects.get(name="music pack vol.33").delete()
	UnlockTask.objects.get(name="music pack vol.34").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0199_tripletribe_s4_convert')]
	operations = [migrations.RunPython(forward, backward)]
