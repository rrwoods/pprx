from django.db import migrations, models

def forward(apps, schema_editor):
	Cabinet = apps.get_model("scorebrowser", "Cabinet")
	gold_cab = Cabinet.objects.get(name="Gold")
	gold_cab.gold = True
	gold_cab.save()



def backward(apps, schema_editor):
	pass # this is not destructive it doesn't matter


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0034_auto_20230317_1914')]

	operations = [migrations.RunPython(forward, backward)]