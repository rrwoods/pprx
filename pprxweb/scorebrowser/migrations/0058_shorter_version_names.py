from django.db import migrations, models

def forward(apps, schema_editor):
	Version = apps.get_model("scorebrowser", "Version")
	Version.objects.filter(id=1).update(name="1st")
	Version.objects.filter(id=2).update(name="2nd")
	Version.objects.filter(id=3).update(name="3rd")
	Version.objects.filter(id=4).update(name="4th")
	Version.objects.filter(id=5).update(name="5th")
	Version.objects.filter(id=6).update(name="MAX")
	Version.objects.filter(id=7).update(name="MAX2")
	Version.objects.filter(id=8).update(name="Extreme")
	Version.objects.filter(id=9).update(name="SuperNOVA")
	Version.objects.filter(id=10).update(name="SuperNOVA2")
	Version.objects.filter(id=11).update(name="X")
	Version.objects.filter(id=12).update(name="X2")
	Version.objects.filter(id=13).update(name="X3 vs 2nd")
	Version.objects.filter(id=14).update(name="2013")
	Version.objects.filter(id=15).update(name="2014")
	Version.objects.filter(id=16).update(name="A")
	Version.objects.filter(id=17).update(name="A20")
	Version.objects.filter(id=18).update(name="A20 PLUS")
	Version.objects.filter(id=19).update(name="A3")

def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0057_gp7_jubeat1_jubeat2_unlocked')]
	operations = [migrations.RunPython(forward, backward)]
