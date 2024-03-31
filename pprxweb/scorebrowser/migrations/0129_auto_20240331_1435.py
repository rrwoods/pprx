# Generated by Django 3.2.16 on 2024-03-31 21:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scorebrowser', '0128_user_django_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pulling_scores',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='webhooked',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='UserScore',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('score', models.IntegerField()),
                ('clear_type', models.IntegerField()),
                ('timestamp', models.IntegerField()),
                ('current', models.BooleanField(null=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.chart')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scorebrowser.user')),
            ],
        ),
        migrations.AddConstraint(
            model_name='userscore',
            constraint=models.UniqueConstraint(fields=('user', 'chart', 'current'), name='uniq_current_score'),
        ),
    ]
