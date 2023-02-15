from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")

	STRANGE = UnlockTask.objects.filter(name="STRANGE").first()
	STRANGE.name = "STRANGE (unlocks Bang Pad(Werk Mix))"
	STRANGE.save()
	
	REMIXES = UnlockTask.objects.filter(name="REMIXES").first()
	REMIXES.name = "REMIXES (unlocks Inner Spirit -GIGA HiTECH MIX-)"
	REMIXES.save()
	
	RAVE = UnlockTask.objects.filter(name="RAVE").first()
	RAVE.name = "RAVE (unlocks Rave Accelerator)"
	RAVE.save()
	
	DIVA = UnlockTask.objects.filter(name="DIVA").first()
	DIVA.name = "DIVA (unlocks Twinkle Wonderland)"
	DIVA.save()
	
	AGGRESSIVE = UnlockTask.objects.filter(name="AGGRESSIVE").first()
	AGGRESSIVE.name = "AGGRESSIVE (unlocks Vertigo)"
	AGGRESSIVE.save()
	
	SNOW = UnlockTask.objects.filter(name="SNOW WHITE").first()
	SNOW.name = "SNOW WHITE (unlocks 梅雪夜)"
	SNOW.save()
	
	PARTY = UnlockTask.objects.filter(name="PARTY ANTHEMS").first()
	PARTY.name = "PARTY ANTHEMS (unlocks PARTY ALL NIGHT(DJ KEN-BOW MIX))"
	PARTY.save()
	
	FANTASY = UnlockTask.objects.filter(name="FANTASY").first()
	FANTASY.name = "FANTASY (unlocks 彼方のリフレシア)"
	FANTASY.save()
	
	NIGHT = UnlockTask.objects.filter(name="NIGHT DRIVE").first()
	NIGHT.name = "NIGHT DRIVE (unlocks Next Phase)"
	NIGHT.save()
	
	FUTURE = UnlockTask.objects.filter(name="FUTURE").first()
	FUTURE.name = "FUTURE (unlocks If)"
	FUTURE.save()
	
	JUST = UnlockTask.objects.filter(name="JUST = 135").first()
	JUST.name = "JUST = 135 (unlocks Taking It To The Sky (PLUS step))"
	JUST.save()
	
	TRIBAL = UnlockTask.objects.filter(name="TRIBAL").first()
	TRIBAL.name = "TRIBAL (unlocks Jucunda Memoria)"
	TRIBAL.save()
	
	SWEETS = UnlockTask.objects.filter(name="SWEETS HOPPING").first()
	SWEETS.name = "SWEETS HOPPING (unlocks Sweet Clock)"
	SWEETS.save()
	
	MACHINE = UnlockTask.objects.filter(name="MACHINE").first()
	MACHINE.name = "MACHINE (unlocks AI)"
	MACHINE.save()
	
	STELLA = UnlockTask.objects.filter(name="STELLA").first()
	STELLA.name = "STELLA (unlocks ほしのつくりかた)"
	STELLA.save()
	
	NEW = UnlockTask.objects.filter(name="NEW STRADE").first()
	NEW.name = "NEW STRADE (unlocks モノクロモーメント)"
	NEW.save()
	
	KATAKANA = UnlockTask.objects.filter(name="KA・TA・KA・NA YEAH!").first()
	KATAKANA.name = "KA・TA・KA・NA YEAH! (unlocks パピポペピプペパ)"
	KATAKANA.save()
	
	WITHSTAND = UnlockTask.objects.filter(name="WITHSTAND").first()
	WITHSTAND.name = "WITHSTAND (unlocks SCHWARZSCHILD FIELD)"
	WITHSTAND.save()
	
	Let = UnlockTask.objects.filter(name="Let's DANCE!").first()
	Let.name = "Let's DANCE! (unlocks 私をディスコに連れてって TOKYO)"
	Let.save()

	TRIPLET = UnlockTask.objects.filter(name="TRIPLET").first()
	TRIPLET.name = "TRIPLET (unlocks PERSIAN LAND)"
	TRIPLET.save()
	
	NIPPON = UnlockTask.objects.filter(name="NIPPON-NO-MATSURI").first()
	NIPPON.name = "NIPPON-NO-MATSURI (unlocks ON-DO)"
	NIPPON.save()
	
	FEELING = UnlockTask.objects.filter(name="FEELING").first()
	FEELING.name = "FEELING (unlocks Come Back to Me (Feel It))"
	FEELING.save()
	
	CYBER = UnlockTask.objects.filter(name="CYBER").first()
	CYBER.name = "CYBER (unlocks Debug Dance)"
	CYBER.save()
	
	INTENSE = UnlockTask.objects.filter(name="INTENSE").first()
	INTENSE.name = "INTENSE (unlocks Get it)"
	INTENSE.save()
	
	EXCITING = UnlockTask.objects.filter(name="EXCITING WINTER").first()
	EXCITING.name = "EXCITING WINTER (unlocks Crystarium)"
	EXCITING.save()
	
	SHED = UnlockTask.objects.filter(name="SHED TEARS").first()
	SHED.name = "SHED TEARS (unlocks insist)"
	SHED.save()

def backward(apps, schema_editor):
	pass

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0026_EON_BREAK')]

	operations = [migrations.RunPython(forward, backward)]