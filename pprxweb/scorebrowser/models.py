from django.db import models


class Version(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()


class Song(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, default=1)
    
    title = models.TextField()
    searchable_title = models.TextField(default="")
    romanized_title = models.TextField(default="")
    alternate_title = models.TextField(default="")
    
    removed = models.BooleanField(default=False)

    class Meta:
        db_table = 'songs'


class Difficulty(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'difficulties'


class Chart(models.Model):
    id = models.AutoField(primary_key=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE)
    rating = models.IntegerField()
    spice = models.FloatField(blank=True, null=True)
    tracked = models.BooleanField(default=True)

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


class Region(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    user_default = models.BooleanField(default=False)

def default_region():
    return Region.objects.get(user_default=True).id


# the player_id field here is a 3icecream player ID -- it is *not* a reference to a Player model object.
# the Player model object is used in spice rating computation and is not related to a logged-in User in any way.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    player_id = models.TextField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT, default=default_region)
    access_token = models.TextField(null=True)
    refresh_token = models.TextField(null=True)
    goal_score = models.IntegerField(default=0)
    goal_chart = models.ForeignKey(Chart, on_delete=models.CASCADE, null=True, default=None)
    romanized_titles = models.BooleanField(default=False)

class UserChartNotes(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    notes = models.TextField()

class CabinetModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()


class SongLock(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=True, default=None)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, default=None)
    model = models.ForeignKey(CabinetModel, on_delete=models.CASCADE, null=True, default=None)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)


class Cabinet(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    model = models.ForeignKey(CabinetModel, on_delete=models.CASCADE)
    name = models.TextField()
    gold = models.BooleanField(default=False)


class UnlockEvent(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    ordering = models.IntegerField()
    completable = models.BooleanField(default=True)


class UnlockTask(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(UnlockEvent, on_delete=models.CASCADE)
    name = models.TextField()
    ordering = models.IntegerField()


class ChartUnlock(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    task = models.ForeignKey(UnlockTask, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    extra = models.BooleanField(default=False)


class UserUnlock(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(UnlockTask, on_delete=models.CASCADE)