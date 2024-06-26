from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.19").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.20").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.21").delete()
	UnlockTask.objects.get(name="GRAND PRIX music pack vol.22").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.0").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0138_gp_challenge_gl_white')]
	operations = [migrations.RunPython(forward, backward)]
