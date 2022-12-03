from django.db import migrations, models

def insert_preferences(apps, schema_editor):
	SongVisibility = apps.get_model("scorebrowser", "SongVisibility")
	for i, name in enumerate(['Visible', 'Extra Exclusive', 'Hidden']):
		d = SongVisibility(id=i, name=name)
		d.save()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0004_songvisibility_songvisibilitypreference')]

	operations = [migrations.RunPython(insert_preferences)]