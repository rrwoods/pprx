from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.17").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.18").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0131_mixup_to_extra_savior')]
	operations = [migrations.RunPython(forward, backward)]
