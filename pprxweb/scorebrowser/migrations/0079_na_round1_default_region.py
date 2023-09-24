from django.db import migrations, models

def forward(apps, schema_editor):
	Region = apps.get_model("scorebrowser", "Region")
	naRound1 = Region.objects.filter(name="North America (Round 1), and Hawaii").first()
	naRound1.user_default = True
	naRound1.save()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0078_region_user_default')]

	operations = [migrations.RunPython(forward, backward)]