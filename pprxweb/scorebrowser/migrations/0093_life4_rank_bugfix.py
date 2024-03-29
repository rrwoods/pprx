# Generated by Django 3.2.16 on 2023-10-31 02:52

from django.db import migrations


def forward(apps, schema_editor):
    UnlockEvent = apps.get_model("scorebrowser", "UnlockEvent")
    SongLock = apps.get_model("scorebrowser", "SongLock")
    Song = apps.get_model("scorebrowser", "Song")
    CabinetModel = apps.get_model("scorebrowser", "CabinetModel")

    extraExclusive = UnlockEvent.objects.get(name="EXTRA EXCLUSIVE")
    extraExclusive.amethyst_required = False
    extraExclusive.save()

    extraExclusive = UnlockEvent.objects.get(name="EXTRA EXCLUSIVE A20PLUS")
    extraExclusive.amethyst_required = False
    extraExclusive.save()

    def findSong(title):
        candidates = Song.objects.filter(title=title)
        for song in candidates:
            if song.title == title:
                return song

    white = CabinetModel.objects.get(name="white")
    for title in [
        'BUTTERFLY (20th Anniversary Mix)',
        'CARTOON HEROES (20th Anniversary Mix)',
        'HAVE YOU NEVER BEEN MELLOW (20th Anniversary Mix)',
        "LONG TRAIN RUNNIN' (20th Anniversary Mix)",
        'SKY HIGH (20th Anniversary Mix)',
    ]:
        SongLock.objects.create(version_id=18, model=white, song=findSong(title))


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0092_mark_required_events'),
    ]

    operations = [
        migrations.RunPython(forward, backward)
    ]
