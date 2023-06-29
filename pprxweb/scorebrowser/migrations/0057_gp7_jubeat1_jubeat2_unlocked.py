from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.7").delete()
	UnlockTask.objects.filter(name="SPECIAL music pack feat.jubeat vol.1").delete()
	UnlockTask.objects.filter(name="SPECIAL music pack feat.jubeat vol.2").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0056_digitalizer_challenge')]
	operations = [migrations.RunPython(forward, backward)]
