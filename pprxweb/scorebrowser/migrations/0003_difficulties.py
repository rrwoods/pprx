from django.db import migrations, models

def insert_difficulties(apps, schema_editor):
	Difficulty = apps.get_model("scorebrowser", "Difficulty")
	for i, name in enumerate(['Beginner', 'Basic', 'Difficult', 'Expert', 'Challenge']):
		d = Difficulty(id=i, name=name)
		d.save()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0002_user')]

	operations = [migrations.RunPython(insert_difficulties)]