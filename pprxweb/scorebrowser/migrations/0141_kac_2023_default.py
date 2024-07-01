from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
	UnlockEvent.objects.get(name="KONAMI Arcade Championship (2023) Entry Songs").delete()

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0140_delete_extra_exclusive')]
	operations = [migrations.RunPython(forward, backward)]
