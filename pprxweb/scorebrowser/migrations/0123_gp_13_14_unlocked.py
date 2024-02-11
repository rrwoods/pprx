from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.13").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.14").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0122_run_the_show_challenge')]
	operations = [migrations.RunPython(forward, backward)]
