from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")
	UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.3").delete()
	UnlockTask.objects.get(name="SPECIAL music pack feat.Touhou Project vol.4").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0170_bemani_selection_1')]
	operations = [migrations.RunPython(forward, backward)]
