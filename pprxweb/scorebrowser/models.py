from django.db import models


class Version(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()


class Song(models.Model):
    id = models.TextField(primary_key=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, default=1)
    title = models.TextField()
    removed = models.BooleanField(default=False)

    class Meta:
        db_table = 'songs'


class Difficulty(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'difficulties'


class Chart(models.Model):
    id = models.AutoField(primary_key=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE)
    rating = models.IntegerField()
    spice = models.FloatField(blank=True, null=True)
    raw_spice = models.FloatField(blank=True, null=True)
    popular = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'charts'


class ChartPair(models.Model):
    id = models.AutoField(primary_key=True)
    x_chart = models.ForeignKey(Chart, related_name='x', on_delete=models.CASCADE)
    y_chart = models.ForeignKey(Chart, related_name='y', on_delete=models.CASCADE)
    slope = models.FloatField()
    strength = models.FloatField()

    class Meta:
        db_table = 'chart_pairs'


class UnprocessedPair(models.Model):
    id = models.AutoField(primary_key=True)
    x_chart = models.ForeignKey(Chart, related_name='x_u', on_delete=models.CASCADE)
    y_chart = models.ForeignKey(Chart, related_name='y_u', on_delete=models.CASCADE)

    class Meta:
        db_table = 'unprocessed_pairs'


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'players'


class Score(models.Model):
    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        db_table = 'scores'


class Benchmark(models.Model):
    id = models.AutoField(primary_key=True)
    rating = models.IntegerField()
    description = models.TextField()
    chart = models.ForeignKey(Chart, on_delete=models.PROTECT, null=True)


# the player_id field here is a 3icecream player ID -- it is *not* a reference to a Player model object.
# the Player model object is used in spice rating computation and is not related to a logged-in User in any way.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    player_id = models.TextField()
    access_token = models.TextField(null=True)
    refresh_token = models.TextField(null=True)
    goal_score = models.IntegerField(default=0)
    goal_benchmark = models.ForeignKey(Benchmark, on_delete=models.PROTECT, null=True, default=None)


class SongVisibility(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()


class SongVisibilityPreference(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    hide_challenge_white = models.BooleanField(default=False)
    hide_challenge_gold = models.BooleanField(default=False)
    white_visibility = models.ForeignKey(SongVisibility, related_name='white', on_delete=models.CASCADE, default=0)
    gold_visibility = models.ForeignKey(SongVisibility, related_name='gold', on_delete=models.CASCADE, default=0)
