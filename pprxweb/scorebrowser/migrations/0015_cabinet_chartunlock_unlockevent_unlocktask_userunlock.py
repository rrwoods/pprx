# Generated by Django 3.2.16 on 2023-02-04 19:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0014_chartpair_player_score_unprocessedpair'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnlockEvent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('ordering', models.IntegerField()),
                ('completable', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='UnlockTask',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('ordering', models.IntegerField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.unlockevent')),
            ],
        ),
        migrations.CreateModel(
            name='UserUnlock',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.unlocktask')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.user')),
            ],
        ),
        migrations.CreateModel(
            name='ChartUnlock',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('extra', models.BooleanField(default=False)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.chart')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.unlocktask')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.version')),
            ],
        ),
        migrations.CreateModel(
            name='Cabinet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('color', models.IntegerField()),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.version')),
                ('name', models.TextField()),
            ],
        ),
    ]
