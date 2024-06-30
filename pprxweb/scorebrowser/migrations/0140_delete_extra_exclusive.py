from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="EXTRA EXCLUSIVE").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0139_gp_19_20_21_22_bpl0_unlocked')]
	operations = [migrations.RunPython(forward, backward)]
