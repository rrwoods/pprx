# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ChartPairs(models.Model):
    id = models.AutoField(primary_key=True)
    x_chart_id = models.IntegerField()
    y_chart_id = models.IntegerField()
    slope = models.FloatField()
    strength = models.FloatField()

    class Meta:
        managed = False
        db_table = 'chart_pairs'


class Charts(models.Model):
    id = models.AutoField(primary_key=True)
    song_id = models.TextField()
    difficulty = models.IntegerField()
    rating = models.IntegerField()
    spice = models.FloatField(blank=True, null=True)
    raw_spice = models.FloatField(blank=True, null=True)
    popular = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'charts'


class Players(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = 'players'


class Scores(models.Model):
    id = models.AutoField(primary_key=True)
    player_id = models.IntegerField()
    chart_id = models.IntegerField()
    score = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'scores'


class Songs(models.Model):
    id = models.TextField(primary_key=True)
    title = models.TextField()

    class Meta:
        managed = False
        db_table = 'songs'


class UnprocessedPairs(models.Model):
    id = models.AutoField(primary_key=True)
    x_chart_id = models.IntegerField()
    y_chart_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'unprocessed_pairs'
