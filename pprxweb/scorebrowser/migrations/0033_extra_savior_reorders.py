from django.db import migrations, models

def forward(apps, schema_editor):
	UnlockTask = apps.get_model("scorebrowser", "UnlockTask")

	def reorder(taskName, ordering):
		task = UnlockTask.objects.filter(name=taskName).first()
		task.ordering = ordering
		task.save()

	reorder('東京神話 (Expert 17)', 5)

	reorder('叛逆のディスパレート (Expert 13)', 15)
	reorder('追憶のアリア (Expert 11)', 12)

	reorder('ウソツキ横丁は雨模様 (Expert 11)', 25)
	reorder('Red Cape Theorem (Expert 14)', 40)

	reorder('ノープラン・デイズ (Expert 16)', 1)
	reorder('勇猛無比 (Expert 14)', 2)
	reorder('BLAKE (Expert 14)', 3)
	reorder('High & Low (Expert 16)', 4)
	reorder('ONYX (Expert 14)', 5)
	reorder('paparazzi (Expert 15)', 6)
	reorder('Shout It Out (Expert 15)', 7)
	reorder("Poppin' Soda (Expert 15)", 8)
	reorder('Sword of Vengeance (Expert 16)', 9)
	reorder('TYPHØN (Difficult 14)', 10)
	reorder('TYPHØN (Expert 17)', 11)

	reorder('Midnight Amaretto (Expert 14)', 15)

	reorder('蒼が消えるとき (Expert 12)', 1)
	reorder('狂水一華 (Expert 15)', 2)
	reorder('ノルエピネフリン (Expert 14)', 3)
	reorder('HARD BRAIN (Expert 15)', 4)
	reorder('Jetcoaster Windy (Expert 15)', 5)
	reorder('Last Twilight (Expert 16)', 6)
	reorder('Our Love (Expert 15)', 7)
	reorder('PANIC HOLIC (Expert 16)', 8)
	reorder("Sparkle Smilin' (Expert 14)", 9)

	reorder("鋳鉄の檻 (Expert 13)", 1)
	reorder("スーパー戦湯ババンバーン (Expert 14)", 2)
	reorder("ユメブキ (Expert 15)", 3)
	reorder("Globe Glitter (Expert 15)", 4)
	reorder("LIKE A VAMPIRE (Expert 13)", 5)
	reorder("MOVE! (We Keep It Movin') (Expert 13)", 6)

	reorder("チュッチュ♪マチュピチュ (Expert 14)", 7)
	reorder("斑咲花 (Expert 16)", 8)
	reorder("DUAL STRIKER (Expert 17)", 9)
	reorder("MA・TSU・RI (Expert 13)", 10)

def backward(apps, schema_editor):
	# this does not create or destroy objects, and forward is idempotent
	pass


class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0032_glitch_angel_challenge')]
	operations = [migrations.RunPython(forward, backward)]