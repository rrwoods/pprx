from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.15").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.16").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0124_triple_tribe_2')]
	operations = [migrations.RunPython(forward, backward)]
