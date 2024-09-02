from django.db import migrations

def forward(apps, schema_editor):
    UnlockTask = apps.get_model("scorebrowser", "UnlockTask")

    cccnnn = UnlockTask.objects.get(name="C-C-C-N-N-N (Challenge 0)")
    cccnnn.name = "C-C-C-N-N-N (Challenge 17)"
    cccnnn.save()

    diablosis = UnlockTask.objects.get(name="DIABLOSIS::Nāga (Challenge 0)")
    diablosis.name = "DIABLOSIS::Nāga (Challenge 18)"
    diablosis.save()

def backward(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0152_gp_undertale_unlocked'),
    ]

    operations = [migrations.RunPython(forward, backward)]
