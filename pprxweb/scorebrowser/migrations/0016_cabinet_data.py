from django.db import migrations, models

def forward(apps, schema_editor):
	Cabinet = apps.get_model("scorebrowser", "Cabinet")
	Cabinet.objects.create(version_id=18, color=0, name="White A20 PLUS")
	Cabinet.objects.create(version_id=19, color=0, name="White A3")
	Cabinet.objects.create(version_id=19, color=1, name="Gold A3")

def backward(apps, schema_editor):
	Cabinet = apps.get_model("scorebrowser", "Cabinet")
	Cabinet.objects.all().delete()	

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0015_cabinet_chartunlock_unlockevent_unlocktask_userunlock')]

	operations = [migrations.RunPython(forward, backward)]