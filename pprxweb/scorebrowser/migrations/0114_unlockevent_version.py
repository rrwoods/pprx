# Generated by Django 3.2.16 on 2023-12-24 01:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0113_delete_benchmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='unlockevent',
            name='version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.version'),
        ),
    ]