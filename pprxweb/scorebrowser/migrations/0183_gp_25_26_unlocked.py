from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.25").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.26").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0182_20250607_content')]
	operations = [migrations.RunPython(forward, backward)]
