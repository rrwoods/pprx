# Generated by Django 4.2.7 on 2024-10-12 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0162_chart_low_conf'),
    ]

    operations = [
        migrations.AddField(
            model_name='userscore',
            name='flare_gauge',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
