from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")

	extraSaviorPlus = UnlockEvent.objects.filter(name="EXTRA SAVIOR PLUS").first()
	if extraSaviorPlus:
		extraSaviorPlus.name = "[A20 PLUS] EXTRA SAVIOR PLUS"
		extraSaviorPlus.save()

	courseTrialA3 = UnlockEvent.objects.filter(name="COURSE TRIAL A3").first()
	if courseTrialA3:
		courseTrialA3.name = "[A3] COURSE TRIAL A3"
		courseTrialA3.save()

	extraSaviorA3 = UnlockEvent.objects.filter(name='EXTRA SAVIOR A3').first()
	if extraSaviorA3:
		extraSaviorA3.name = "[A3] EXTRA SAVIOR A3"
		extraSaviorA3.save()

	bandMeshi2 = UnlockEvent.objects.filter(name="バンめし♪ ふるさとグランプリ ROUND 2").first()
	if bandMeshi2:
		bandMeshi2.name = "[A20 PLUS] バンめし♪ ふるさとグランプリ ROUND 2"
		bandMeshi2.save()

	bandMeshi3 = UnlockEvent.objects.filter(name="バンめし♪ ふるさとグランプリ ROUND 3").first()
	if bandMeshi3:
		bandMeshi3.name = "[A20 PLUS] バンめし♪ ふるさとグランプリ ROUND 3"
		bandMeshi3.save()

	trickHalloween = UnlockEvent.objects.filter(name="Trick and DDR! HAPPY HALLOWEEN!!").first()
	if trickHalloween:
		trickHalloween.name = "[A20 PLUS] Trick and DDR! HAPPY HALLOWEEN!!"
		trickHalloween.save()

	christmas2020 = UnlockEvent.objects.filter(name="Merry Christmas and Happy DDR! 2020").first()
	if christmas2020:
		christmas2020.name = "[A20 PLUS] Merry Christmas and Happy DDR! 2020"
		christmas2020.save()

	valentine2021 = UnlockEvent.objects.filter(name="恋せよDDRのバレンタイン＆ホワイトデー2021").first()
	if valentine2021:
		valentine2021.name = "[A20 PLUS] 恋せよDDRのバレンタイン＆ホワイトデー2021"
		valentine2021.save()

	springFestival = UnlockEvent.objects.filter(name='花咲ケ!DDR SPRING FESTIVAL').first()
	if springFestival:
		springFestival.name = '[A20 PLUS] 花咲ケ!DDR SPRING FESTIVAL'
		springFestival.save()

	over200 = UnlockEvent.objects.filter(name="OVER 200").first()
	if over200:
		over200.name = "[A20 PLUS] OVER 200"
		over200.save()

	valentine2022 = UnlockEvent.objects.filter(name='恋せよDDRのバレンタイン＆ホワイトデー2022').first()
	if valentine2022:
		valentine2022.name = '[A20 PLUS] 恋せよDDRのバレンタイン＆ホワイトデー2022'
		valentine2022.save()

	summerCamp = UnlockEvent.objects.filter(name="DANCERUSH STARDOM × DanceDanceRevolution SUMMER DANCE CAMP 2020").first()
	if summerCamp:
		summerCamp.name = "[A20 PLUS] DANCERUSH STARDOM × DanceDanceRevolution SUMMER DANCE CAMP 2020"
		summerCamp.save()

	bemaniRush = UnlockEvent.objects.filter(name="毎週！いちかの超BEMANIラッシュ2020").first()
	if bemaniRush:
		bemaniRush.name = "[A20 PLUS] 毎週！いちかの超BEMANIラッシュ2020"
		bemaniRush.save()

	floorInfection = UnlockEvent.objects.filter(name="FLOOR INFECTION").first()
	if floorInfection:
		floorInfection.name = "[A20 PLUS] FLOOR INFECTION"
		floorInfection.save()

	challengeCarnival = UnlockEvent.objects.filter(name="DDR CHALLENGE Carnival PLUS").first()
	if challengeCarnival:
		challengeCarnival.name = "[A20 PLUS] DDR CHALLENGE Carnival PLUS"
		challengeCarnival.save()

	courseTrial = UnlockEvent.objects.filter(name="COURSE TRIAL").first()
	if courseTrial:
		courseTrial.name = "[A20 PLUS] COURSE TRIAL"
		courseTrial.save()

	kac10 = UnlockEvent.objects.filter(name="The 10th KONAMI Arcade Championship Entry Song").first()
	if kac10:
		kac10.name = "[A20 PLUS] The 10th KONAMI Arcade Championship Entry Song"
		kac10.save()

	bplRally = UnlockEvent.objects.filter(name="BPL応援 楽曲解禁スタンプラリー").first()
	if bplRally:
		bplRally.name = "[A20 PLUS] BPL応援 楽曲解禁スタンプラリー"
		bplRally.save()

	midsummer = UnlockEvent.objects.filter(name="BEMANI 2021真夏の歌合戦5番勝負").first()
	if midsummer:
		midsummer.name = "[A20 PLUS] BEMANI 2021真夏の歌合戦5番勝負"
		midsummer.save()


	summerVacation = UnlockEvent.objects.filter(name='Enjoy Summer Vacation!').first()
	if summerVacation:
		summerVacation.name = "[A3] Enjoy Summer Vacation!"
		summerVacation.save()

	midsummerRedux = UnlockEvent.objects.filter(name='BEMANI 2021真夏の歌合戦5番勝負 [A3]').first()
	if midsummerRedux:
		midsummerRedux.name = "[A3] BEMANI 2021真夏の歌合戦5番勝負"
		midsummerRedux.save()

	crystalClearWinter = UnlockEvent.objects.filter(name='Crystal clear winter').first()
	if crystalClearWinter:
		crystalClearWinter.name = "[A3] Crystal clear winter"
		crystalClearWinter.save()

	valentine2023 = UnlockEvent.objects.filter(name='恋せよDDRのバレンタイン＆ホワイトデー2023').first()
	if valentine2023:
		valentine2023.name = "[A3] 恋せよDDRのバレンタイン＆ホワイトデー2023"
		valentine2023.save()

	musicChoice = UnlockEvent.objects.filter(name="DANCE aROUND × DanceDanceRevolution 2022 natsu no MUSIC CHOICE").first()
	if musicChoice:
		musicChoice.name = "[A3] DANCE aROUND × DanceDanceRevolution 2022 natsu no MUSIC CHOICE"
		musicChoice.save()

	mixUp = UnlockEvent.objects.filter(name="いちかのごちゃまぜMix UP！").first()
	if mixUp:
		mixUp.name = "[A3] いちかのごちゃまぜMix UP！"
		mixUp.save()

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0024_migrate_goals_to_charts')]

	operations = [migrations.RunPython(forward, backward)]