# Generated by Django 3.2.16 on 2022-12-07 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0011_auto_20221206_2112'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='goal_score',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='Benchmark',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('rating', models.IntegerField()),
                ('description', models.TextField()),
                ('chart', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='scorebrowser.chart')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='goal_benchmark',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='scorebrowser.benchmark'),
        ),
    ]
