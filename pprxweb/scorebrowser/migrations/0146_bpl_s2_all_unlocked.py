from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="BPL S2 music pack vol.1 (Aria)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.2 (Rise As One)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.3 (Drive Away)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.4 (Chromatic Burst)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.5 (GLOW THE CROWN)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.6 (SMASH)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.7 (Complete Game Victory)").delete()
	UnlockTask.objects.get(name="BPL S2 music pack vol.8 (Abrupt Madness)").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0145_chart_hidden')]
	operations = [migrations.RunPython(forward, backward)]
