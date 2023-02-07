from django.db import migrations, models

def forward(apps, schema_editor):
	Region = apps.get_model("scorebrowser", "Region")
	northAmerica = Region.objects.create(name="North America")
	hawaii = Region.objects.create(name="Hawaii")
	japan = Region.objects.create(name="Japan")

	CabinetModel = apps.get_model("scorebrowser", "CabinetModel")
	white = CabinetModel.objects.create(name="white")
	gold = CabinetModel.objects.create(name="gold")

	Cabinet = apps.get_model("scorebrowser", "Cabinet")
	Cabinet.objects.create(version_id=18, region=northAmerica, model=white, name="White A20PLUS (North America)")
	Cabinet.objects.create(version_id=19, region=hawaii, model=white, name="White A3 (Hawaii)")
	Cabinet.objects.create(version_id=19, region=japan, model=white, name="White A3 (Japan)")
	Cabinet.objects.create(version_id=19, region=japan, model=gold, name="Gold")

	Song = apps.get_model("scorebrowser", "Song")
	def findSong(title):
		return Song.objects.filter(title=title).first()

	SongLock = apps.get_model("scorebrowser", "SongLock")

	SongLock.objects.create(version_id=18, model=white, song=findSong("Lightspeed"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Run The Show"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Yuni's Nocturnal Days"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Good Looking"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Step This Way"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Come Back To Me"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("actualization of self (weaponized)"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("Better Than Me"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("DDR TAGMIX -LAST DanceR-"))
	SongLock.objects.create(version_id=18, model=white, song=findSong("THIS IS MY LAST RESORT"))

	SongLock.objects.create(version_id=19, model=white, song=findSong("Environ [De-SYNC] (feat. lythe)"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Let Me Know"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Let Me Show You"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Go To The Oasis"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("TAKE ME HIGHER"))
	SongLock.objects.create(version_id=19, model=white, song=findSong("Lose Your Sense"))

	SongLock.objects.create(model=white, song=findSong("HAVE YOU NEVER BEEN MELLOW (20th Anniversary Mix)"))
	SongLock.objects.create(model=white, song=findSong("CARTOON HEROES (20th Anniversary Mix)"))
	SongLock.objects.create(model=white, song=findSong("LONG TRAIN RUNNIN' (20th Anniversary Mix)"))
	SongLock.objects.create(model=white, song=findSong("SKY HIGH (20th Anniversary Mix)"))
	SongLock.objects.create(model=white, song=findSong("BUTTERFLY (20th Anniversary Mix)"))

	SongLock.objects.create(region=northAmerica, song=findSong("最終鬼畜妹フランドール・Ｓ"))
	SongLock.objects.create(region=northAmerica, song=findSong("ナイト・オブ・ナイツ (Ryu☆Remix)"))
	
	SongLock.objects.create(region=northAmerica, song=findSong("Crazy Hot"))
	SongLock.objects.create(region=northAmerica, song=findSong("Feidie"))
	SongLock.objects.create(region=northAmerica, song=findSong("GUILTY DIAMONDS"))
	SongLock.objects.create(region=northAmerica, song=findSong("No Life Queen [DJ Command Remix]"))
	SongLock.objects.create(region=northAmerica, song=findSong("Together Going My Way"))
	SongLock.objects.create(region=northAmerica, song=findSong("SHINY DAYS"))
	SongLock.objects.create(region=northAmerica, song=findSong("春を告げる"))
	SongLock.objects.create(region=northAmerica, song=findSong("なだめスかし Negotiation"))
	SongLock.objects.create(region=northAmerica, song=findSong("I believe what you said"))
	SongLock.objects.create(region=northAmerica, song=findSong("Realize"))
	SongLock.objects.create(region=northAmerica, song=findSong("思想犯"))
	SongLock.objects.create(region=northAmerica, song=findSong("Seize The Day"))
	SongLock.objects.create(region=northAmerica, song=findSong("スカイクラッドの観測者"))
	SongLock.objects.create(region=northAmerica, song=findSong("雑草魂なめんなよ！"))
	SongLock.objects.create(region=northAmerica, song=findSong("恋"))
	SongLock.objects.create(region=northAmerica, song=findSong("ロキ(w/緒方恵美)"))
	SongLock.objects.create(region=northAmerica, song=findSong("シル・ヴ・プレジデント"))
	SongLock.objects.create(region=northAmerica, song=findSong("サイカ"))
	SongLock.objects.create(region=northAmerica, song=findSong("テレキャスタービーボーイ"))

def backward(apps, schema_editor):
	Cabinet = apps.get_model("scorebrowser", "Cabinet")
	Cabinet.objects.all().delete()

	SongLock = apps.get_model("scorebrowser", "SongLock")
	SongLock.objects.all().delete()

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0020_cabinet')]

	operations = [migrations.RunPython(forward, backward)]