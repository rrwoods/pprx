from django.contrib.auth.models import User as DjangoUser
from django.db import models


class Version(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()


class Song(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, default=1)
    
    title = models.TextField()
    sort_key = models.TextField(default="")
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
    rerate = models.IntegerField(null=True, default=None)  # for "manual" re-rates, when automatically-updated data is slow to arrive
    spice = models.FloatField(blank=True, null=True)
    low_conf = models.BooleanField(default=False)
    normscore_breakpoints = models.TextField(default="")
    quality_breakpoints = models.TextField(default="")
    tracked = models.BooleanField(default=True)
    hidden = models.BooleanField(default=False)

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


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'players'


class Score(models.Model):
    # represents a scraped public score -- NOT a PPR X user's score.
    # for PPR X users' scores, see UserScore.
    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    score = models.IntegerField()
    normalized = models.FloatField(default=0)

    class Meta:
        db_table = 'scores'


class Region(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    user_default = models.BooleanField(default=False)

def default_region():
    return Region.objects.get(user_default=True).id


class ProfileVisibility(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField(default="")


# the player_id field here is a 3icecream player ID -- it is *not* a reference to a Player model object.
# the Player model object is used in spice rating computation and is not related to a logged-in User in any way.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    django_user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, null=True, default=None)
    visibility = models.ForeignKey(ProfileVisibility, on_delete=models.SET_DEFAULT, default=0)

    player_id = models.TextField()
    access_token = models.TextField(null=True)
    refresh_token = models.TextField(null=True)
    webhooked = models.BooleanField(default=False)
    reauth = models.BooleanField(default=False)
    pulling_scores = models.BooleanField(default=False)

    region = models.ForeignKey(Region, on_delete=models.PROTECT, default=default_region)
    goal_score = models.IntegerField(default=0)
    goal_chart = models.ForeignKey(Chart, on_delete=models.CASCADE, null=True, default=None)
    romanized_titles = models.BooleanField(default=False)

    selected_rank = models.IntegerField(default=0)
    selected_flare = models.IntegerField(default=0)
    best_trial = models.IntegerField(default=0)
    second_best_trial = models.IntegerField(default=0)
    best_two_consecutive = models.IntegerField(default=0)
    best_three_consecutive = models.IntegerField(default=0)
    best_calorie_burn = models.IntegerField(default=0)


class UserScore(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)

    score = models.IntegerField()
    normalized = models.FloatField(default=0)
    quality = models.FloatField(null=True, default=None)

    clear_type = models.IntegerField()
    flare_gauge = models.IntegerField(null=True, default=None)
    
    timestamp = models.IntegerField()
    current = models.BooleanField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ['user', 'chart', 'current'],
                name = 'uniq_current_score',
            )
        ]

class UserChartAux(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    bookmark = models.BooleanField(default=False)
    notes = models.TextField(default='')
    life4_clear = models.BooleanField(default=False)

class UserRequirementTarget(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    goal_id = models.IntegerField()

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


class UnlockGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    ordering = models.IntegerField()


class UnlockEvent(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    group = models.ForeignKey(UnlockGroup, on_delete=models.CASCADE, null=True)
    name = models.TextField()
    progressive = models.BooleanField(default=False)
    ordering = models.IntegerField()
    amethyst_required = models.BooleanField(default=True)


class UnlockTask(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(UnlockEvent, on_delete=models.CASCADE)
    name = models.TextField()
    ordering = models.IntegerField()


class ChartUnlock(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(UnlockTask, on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
    extra = models.BooleanField(default=False)


class UserUnlock(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(UnlockTask, on_delete=models.CASCADE)

class UserProgressiveUnlock(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(UnlockTask, on_delete=models.CASCADE)
    event = models.ForeignKey(UnlockEvent, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ['user', 'event'],
                name = 'uniq_progressive',
            )
        ]