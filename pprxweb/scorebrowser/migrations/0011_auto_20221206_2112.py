# Generated by Django 3.2.16 on 2022-12-07 05:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0010_song_removed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chart',
            name='difficulty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.difficulty'),
        ),
        migrations.AlterField(
            model_name='chart',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.song'),
        ),
        migrations.AlterField(
            model_name='song',
            name='version',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.version'),
        ),
        migrations.AlterField(
            model_name='songvisibilitypreference',
            name='gold_visibility',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='gold', to='scorebrowser.songvisibility'),
        ),
        migrations.AlterField(
            model_name='songvisibilitypreference',
            name='white_visibility',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='white', to='scorebrowser.songvisibility'),
        ),
    ]
