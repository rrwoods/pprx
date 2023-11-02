# Generated by Django 3.2.16 on 2023-10-26 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0089_userchartaux_life4_clear'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='best_calorie_burn',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='best_three_consecutive',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='best_trial',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='best_two_consecutive',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='second_best_trial',
            field=models.IntegerField(default=0),
        ),
    ]