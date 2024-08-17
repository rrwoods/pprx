from django.db import migrations, models

def forward(apps, schema_editor):
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")

    shDsp = UnlockTask.objects.get(name='SUPER HEROINE!! (Difficult 8)')
    shDsp.ordering = 33
    shDsp.save()

    shEsp = UnlockTask.objects.get(name='SUPER HEROINE!! (Expert 13)')
    shEsp.ordering = 36
    shEsp.save()

    hideBsp = UnlockTask.objects.get(name='残像ニ繋ガレタ追憶ノHIDEAWAY (Basic 7)')
    hideBsp.ordering = 95
    hideBsp.save()

    hideEsp = UnlockTask.objects.get(name='残像ニ繋ガレタ追憶ノHIDEAWAY (Expert 15)')
    hideEsp.ordering = 120
    hideEsp.save()

    dsbsp = UnlockTask.objects.get(name='弾幕信仰 (Beginner 3)')
    dsbsp.ordering = 130
    dsbsp.save()

    dsBsp = UnlockTask.objects.get(name='弾幕信仰 (Basic 6)')
    dsBsp.ordering = 140
    dsBsp.save()

    dsDsp = UnlockTask.objects.get(name='弾幕信仰 (Difficult 10)')
    dsDsp.ordering = 150
    dsDsp.save()

    dsEsp = UnlockTask.objects.get(name='弾幕信仰 (Expert 16)')
    dsEsp.ordering = 160
    dsEsp.save()


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0149_userprogressiveunlock_and_more'),
    ]

    operations = [migrations.RunPython(forward, backward)]
