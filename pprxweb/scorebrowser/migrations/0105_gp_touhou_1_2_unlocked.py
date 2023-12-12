from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.1").delete()
	UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.2").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0104_course_trial_piano_melody')]
	operations = [migrations.RunPython(forward, backward)]
