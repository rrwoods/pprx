import uuid
from django.contrib.auth.models import User as DjangoUser
from scorebrowser.models import (
    Chart,
    ChartPair,
    ChartUnlock,
    Difficulty,
    Player,
    Score,
    Song,
    SongLock,
    UnlockEvent,
    UnlockGroup,
    UnlockTask,
    User,
    UserScore,
    UserUnlock,
    Version,
)
from .fakes import FakeScoreSource


def create_song(id=None, version=None, title=None, **kwargs):
    if version is None and 'version_id' not in kwargs:
        version = Version.objects.order_by('id').last()
    if id is None:
        id = f"song_{uuid.uuid4().hex[:16]}"
    if title is None:
        title = f"Song {id}"
    song_kwargs = {'id': id, 'title': title, **kwargs}
    if version is not None:
        song_kwargs['version'] = version
    return Song.objects.create(**song_kwargs)


def create_chart(song=None, difficulty=None, rating=10, hidden=False, **kwargs):
    if song is None and 'song_id' not in kwargs:
        song = create_song()
    if difficulty is None and 'difficulty_id' not in kwargs:
        difficulty = Difficulty.objects.get(name="Expert")
    chart_kwargs = {
        'rating': rating,
        'hidden': hidden,
        **kwargs,
    }
    if song is not None:
        chart_kwargs['song'] = song
    if difficulty is not None:
        chart_kwargs['difficulty'] = difficulty
    return Chart.objects.create(**chart_kwargs)


def create_song_lock(song=None, **kwargs):
    if song is None and 'song_id' not in kwargs:
        song = create_song()
    lock_kwargs = dict(kwargs)
    if song is not None:
        lock_kwargs['song'] = song
    return SongLock.objects.create(**lock_kwargs)


def create_unlock_group(name=None, ordering=0, **kwargs):
    if name is None:
        name = f"Unlock Group {uuid.uuid4().hex[:8]}"
    return UnlockGroup.objects.create(name=name, ordering=ordering, **kwargs)


def create_unlock_event(version=None, group=None, name=None, ordering=0, **kwargs):
    if version is None and 'version_id' not in kwargs:
        version = Version.objects.order_by('id').last()
    if name is None:
        name = f"Unlock Event {uuid.uuid4().hex[:8]}"
    event_kwargs = {
        'name': name,
        'ordering': ordering,
        **kwargs,
    }
    if version is not None:
        event_kwargs['version'] = version
    if group is not None:
        event_kwargs['group'] = group
    return UnlockEvent.objects.create(**event_kwargs)


def create_unlock_task(event=None, name=None, ordering=0, **kwargs):
    if event is None and 'event_id' not in kwargs:
        event = create_unlock_event()
    if name is None:
        name = f"Unlock Task {uuid.uuid4().hex[:8]}"
    task_kwargs = {
        'name': name,
        'ordering': ordering,
        **kwargs,
    }
    if event is not None:
        task_kwargs['event'] = event
    return UnlockTask.objects.create(**task_kwargs)


def create_chart_unlock(task=None, chart=None, extra=False, **kwargs):
    if task is None and 'task_id' not in kwargs:
        task = create_unlock_task()
    if chart is None and 'chart_id' not in kwargs:
        chart = create_chart()
    chart_unlock_kwargs = {
        'extra': extra,
        **kwargs,
    }
    if task is not None:
        chart_unlock_kwargs['task'] = task
    if chart is not None:
        chart_unlock_kwargs['chart'] = chart
    return ChartUnlock.objects.create(**chart_unlock_kwargs)


def create_user(player_id=None, with_django_user=False, **kwargs):
    if player_id is None:
        player_id = f"user_{uuid.uuid4().hex[:12]}"
    user_kwargs = dict(kwargs)
    if with_django_user:
        username = f"user_{player_id}"
        user_kwargs['django_user'] = DjangoUser.objects.create_user(username=username)
    return User.objects.create(player_id=player_id, **user_kwargs)


def create_user_score(
    user=None,
    chart=None,
    score=900000,
    clear_type=1,
    timestamp=1000000,
    current=True,
    **kwargs,
):
    if user is None and 'user_id' not in kwargs:
        user = create_user()
    if chart is None and 'chart_id' not in kwargs:
        chart = create_chart()
    user_score_kwargs = {
        'score': score,
        'clear_type': clear_type,
        'timestamp': timestamp,
        'current': current,
        **kwargs,
    }
    if user is not None:
        user_score_kwargs['user'] = user
    if chart is not None:
        user_score_kwargs['chart'] = chart
    return UserScore.objects.create(**user_score_kwargs)


def create_user_unlock(user=None, task=None, **kwargs):
    if user is None and 'user_id' not in kwargs:
        user = create_user()
    if task is None and 'task_id' not in kwargs:
        task = create_unlock_task()
    unlock_kwargs = dict(kwargs)
    if user is not None:
        unlock_kwargs['user'] = user
    if task is not None:
        unlock_kwargs['task'] = task
    return UserUnlock.objects.create(**unlock_kwargs)


def create_player(name=None, **kwargs):
    if name is None:
        name = f"Player {uuid.uuid4().hex[:8]}"
    return Player.objects.create(name=name, **kwargs)


def create_score(player=None, chart=None, score=900000, **kwargs):
    if player is None and 'player_id' not in kwargs:
        player = create_player()
    if chart is None and 'chart_id' not in kwargs:
        chart = create_chart()
    score_kwargs = {
        'score': score,
        **kwargs,
    }
    if player is not None:
        score_kwargs['player'] = player
    if chart is not None:
        score_kwargs['chart'] = chart
    return Score.objects.create(**score_kwargs)


def create_chart_pair(x_chart=None, y_chart=None, slope=1.0, strength=1.0, **kwargs):
    if x_chart is None and 'x_chart_id' not in kwargs:
        x_chart = create_chart()
    if y_chart is None and 'y_chart_id' not in kwargs:
        y_chart = create_chart()
    pair_kwargs = {
        'slope': slope,
        'strength': strength,
        **kwargs,
    }
    if x_chart is not None:
        pair_kwargs['x_chart'] = x_chart
    if y_chart is not None:
        pair_kwargs['y_chart'] = y_chart
    return ChartPair.objects.create(**pair_kwargs)
