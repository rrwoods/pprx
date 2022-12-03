from django.db import migrations, models

def insert_versions(apps, schema_editor):
	Version = apps.get_model("scorebrowser", "Version")
	for name in [
		'DDR 1st',
		'DDR 2ndMIX',
		'DDR 3rdMIX',
		'DDR 4thMIX',
		'DDR 5thMIX',
		'DDRMAX',
		'DDRMAX2',
		'DDR EXTREME',
		'DDR SuperNOVA',
		'DDR SuperNOVA 2',
		'DDR X',
		'DDR X2',
		'DDR X3 VS 2ndMIX',
		'DanceDanceRevolution(2013)',
		'DanceDanceRevolution(2014)',
		'DDR A',
		'DDR A20',
		'DDR A20 PLUS',
		'DDR A3',
	]:
		v = Version(name=name)
		v.save()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0006_version')]

	operations = [migrations.RunPython(insert_versions)]