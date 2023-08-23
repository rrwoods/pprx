from django.db import migrations, models

def forward(apps, schema_editor):
	SongLock = apps.get_model("scorebrowser", "SongLock")
	User = apps.get_model("scorebrowser", "User")
	Region = apps.get_model("scorebrowser", "Region")
	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")
	Song = apps.get_model("scorebrowser", "Song")

	gold = CabinetModel.objects.get(name="gold")
	for title in ['C-C-C-N-N-N', 'DIABLOSIS::Nāga', 'suspicions']:
		song = Song.objects.get(title=title)
		SongLock.objects.create(model=gold, song=song)

	tdx = Region.objects.get(name="Hawaii")
	tdx.name = "North America (Round 1), and Hawaii"
	tdx.save()

	mdx = Region.objects.get(name="North America")
	mdx.name = "North America (Dave & Buster's)"
	mdx.save()

	User.objects.filter(region=mdx).update(region=tdx)


def backward(apps, schema_editor):
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0068_triple_tribe')]

	operations = [migrations.RunPython(forward, backward)]