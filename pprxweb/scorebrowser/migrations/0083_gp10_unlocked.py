from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.filter(name="GRAND PRIX music pack vol.10").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0082_userchartnotes')]
	operations = [migrations.RunPython(forward, backward)]
