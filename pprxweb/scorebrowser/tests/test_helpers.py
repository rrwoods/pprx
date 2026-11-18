from django.contrib.auth.models import User as DjangoUser
from scorebrowser.models import (
    Cabinet,
    CabinetModel,
    Chart,
    ChartPair,
    ChartUnlock,
    Difficulty,
    Player,
    ProfileVisibility,
    Region,
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
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.helpers import (
    create_chart,
    create_chart_pair,
    create_chart_unlock,
    create_player,
    create_score,
    create_song,
    create_song_lock,
    create_unlock_event,
    create_unlock_group,
    create_unlock_task,
    create_user,
    create_user_score,
    create_user_unlock,
)


class HelperTests(PPRXTestCase):
    def test_create_chart_defaults(self):
        chart = create_chart()
        self.assertFalse(chart.hidden)
        self.assertEqual(chart.difficulty.name, "Expert")
        current_version = Version.objects.order_by('id').last()
        self.assertEqual(chart.song.version, current_version)

    def test_create_chart_overrides(self):
        challenge = Difficulty.objects.get(name="Challenge")
        chart = create_chart(hidden=True, difficulty=challenge, rating=18)
        self.assertTrue(chart.hidden)
        self.assertEqual(chart.difficulty, challenge)
        self.assertEqual(chart.rating, 18)

    def test_create_song_defaults_and_overrides(self):
        song = create_song()
        current_version = Version.objects.order_by('id').last()
        self.assertEqual(song.version, current_version)
        self.assertTrue(song.id.startswith("song_"))
        self.assertEqual(song.title, f"Song {song.id}")

        custom_version = Version.objects.first()
        override_song = create_song(
            id="custom_id",
            version=custom_version,
            title="Custom Title",
        )
        self.assertEqual(override_song.id, "custom_id")
        self.assertEqual(override_song.version, custom_version)
        self.assertEqual(override_song.title, "Custom Title")

    def test_create_chart_unlock_defaults_builds_required_parents_and_nothing_more(self):
        chart_unlock = create_chart_unlock()

        self.assertFalse(chart_unlock.extra)
        self.assertIsNotNone(chart_unlock.task)
        self.assertIsNotNone(chart_unlock.task.event)
        self.assertIsNone(chart_unlock.task.event.group)
        self.assertIsNotNone(chart_unlock.chart)
        self.assertIsNotNone(chart_unlock.chart.song)

        current_version = Version.objects.order_by('id').last()
        self.assertEqual(chart_unlock.task.event.version, current_version)
        self.assertEqual(chart_unlock.chart.song.version, current_version)

        self.assertEqual(Song.objects.count(), 1)
        self.assertEqual(Chart.objects.count(), 1)
        self.assertEqual(SongLock.objects.count(), 0)
        self.assertEqual(UnlockGroup.objects.count(), 0)
        # UnlockEvent and UnlockTask have 1 row from setUpTestData (the A3+ exception), plus 1 created
        self.assertEqual(UnlockEvent.objects.count(), 2)
        self.assertEqual(UnlockTask.objects.count(), 2)
        self.assertEqual(ChartUnlock.objects.count(), 1)

    def test_create_song_lock_defaults_and_overrides(self):
        lock = create_song_lock()
        self.assertIsNotNone(lock.song)
        self.assertIsNone(lock.version)
        self.assertIsNone(lock.region)
        self.assertIsNone(lock.model)

        song = create_song()
        version = Version.objects.first()
        region = Region.objects.first()
        model = CabinetModel.objects.first()
        custom_lock = create_song_lock(
            song=song,
            version=version,
            region=region,
            model=model,
        )
        self.assertEqual(custom_lock.song, song)
        self.assertEqual(custom_lock.version, version)
        self.assertEqual(custom_lock.region, region)
        self.assertEqual(custom_lock.model, model)

    def test_create_unlock_group_defaults_and_overrides(self):
        group = create_unlock_group()
        self.assertTrue(group.name.startswith("Unlock Group "))
        self.assertEqual(group.ordering, 0)

        custom_group = create_unlock_group(name="Custom Group", ordering=5)
        self.assertEqual(custom_group.name, "Custom Group")
        self.assertEqual(custom_group.ordering, 5)

    def test_create_unlock_event_defaults_and_overrides(self):
        event = create_unlock_event()
        current_version = Version.objects.order_by('id').last()
        self.assertEqual(event.version, current_version)
        self.assertIsNone(event.group)
        self.assertTrue(event.name.startswith("Unlock Event "))
        self.assertEqual(event.ordering, 0)
        self.assertFalse(event.progressive)
        self.assertFalse(event.amethyst_required)

        custom_version = Version.objects.first()
        group = create_unlock_group()
        custom_event = create_unlock_event(
            version=custom_version,
            group=group,
            name="Custom Event",
            ordering=3,
            progressive=True,
            amethyst_required=True,
        )
        self.assertEqual(custom_event.version, custom_version)
        self.assertEqual(custom_event.group, group)
        self.assertEqual(custom_event.name, "Custom Event")
        self.assertEqual(custom_event.ordering, 3)
        self.assertTrue(custom_event.progressive)
        self.assertTrue(custom_event.amethyst_required)

        # Overriding group via group_id works without being clobbered by default None
        event_by_group_id = create_unlock_event(group_id=group.id)
        self.assertEqual(event_by_group_id.group, group)

    def test_create_unlock_task_defaults_and_overrides(self):
        task = create_unlock_task()
        self.assertIsNotNone(task.event)
        self.assertTrue(task.name.startswith("Unlock Task "))
        self.assertEqual(task.ordering, 0)

        event = create_unlock_event()
        custom_task = create_unlock_task(event=event, name="Custom Task", ordering=7)
        self.assertEqual(custom_task.event, event)
        self.assertEqual(custom_task.name, "Custom Task")
        self.assertEqual(custom_task.ordering, 7)

        empty_name_task = create_unlock_task(name="")
        self.assertEqual(empty_name_task.name, "")

    def test_create_chart_unlock_overrides(self):
        task = create_unlock_task()
        chart = create_chart()
        custom_unlock = create_chart_unlock(task=task, chart=chart, extra=True)
        self.assertEqual(custom_unlock.task, task)
        self.assertEqual(custom_unlock.chart, chart)
        self.assertTrue(custom_unlock.extra)

    def test_create_user_defaults_and_linked_django_user_only_on_request(self):
        user = create_user()
        self.assertEqual(user.visibility.id, 0)
        self.assertEqual(user.visibility.name, "Private")
        default_region = Region.objects.get(user_default=True)
        self.assertEqual(user.region, default_region)
        self.assertTrue(user.player_id.startswith("user_"))
        self.assertIsNone(user.django_user)
        self.assertEqual(DjangoUser.objects.count(), 0)

        user_with_auth = create_user(with_django_user=True)
        self.assertIsNotNone(user_with_auth.django_user)
        self.assertEqual(DjangoUser.objects.count(), 1)
        self.assertEqual(user_with_auth.django_user.username, f"user_{user_with_auth.player_id}")

        custom_visibility = ProfileVisibility.objects.get(id=1)
        non_default_region = Region.objects.exclude(user_default=True).first()
        custom_user = create_user(
            player_id="custom_user",
            visibility=custom_visibility,
            region=non_default_region,
            romanized_titles=True,
        )
        self.assertEqual(custom_user.player_id, "custom_user")
        self.assertEqual(custom_user.visibility, custom_visibility)
        self.assertEqual(custom_user.region, non_default_region)
        self.assertTrue(custom_user.romanized_titles)

    def test_create_user_score_defaults_and_overrides(self):
        user_score = create_user_score()
        self.assertIsNotNone(user_score.user)
        self.assertIsNotNone(user_score.chart)
        self.assertEqual(user_score.score, 900000)
        self.assertEqual(user_score.clear_type, 1)
        self.assertEqual(user_score.timestamp, 1000000)
        self.assertTrue(user_score.current)

        user = create_user()
        chart = create_chart()
        custom_score = create_user_score(
            user=user,
            chart=chart,
            score=985000,
            clear_type=5,
            timestamp=1234567,
            current=False,
            quality=15.5,
            flare_gauge=9,
        )
        self.assertEqual(custom_score.user, user)
        self.assertEqual(custom_score.chart, chart)
        self.assertEqual(custom_score.score, 985000)
        self.assertEqual(custom_score.clear_type, 5)
        self.assertEqual(custom_score.timestamp, 1234567)
        self.assertFalse(custom_score.current)
        self.assertEqual(custom_score.quality, 15.5)
        self.assertEqual(custom_score.flare_gauge, 9)

    def test_create_user_unlock_defaults_and_overrides(self):
        unlock = create_user_unlock()
        self.assertIsNotNone(unlock.user)
        self.assertIsNotNone(unlock.task)

        user = create_user()
        task = create_unlock_task()
        custom_unlock = create_user_unlock(user=user, task=task)
        self.assertEqual(custom_unlock.user, user)
        self.assertEqual(custom_unlock.task, task)

    def test_create_player_defaults_and_overrides(self):
        player = create_player()
        self.assertTrue(player.name.startswith("Player "))

        custom_player = create_player(name="Custom Player")
        self.assertEqual(custom_player.name, "Custom Player")

    def test_create_score_defaults_and_overrides(self):
        score = create_score()
        self.assertIsNotNone(score.player)
        self.assertIsNotNone(score.chart)
        self.assertEqual(score.score, 900000)
        self.assertEqual(score.normalized, 0)

        player = create_player()
        chart = create_chart()
        custom_score = create_score(
            player=player,
            chart=chart,
            score=990000,
            normalized=-5.2,
        )
        self.assertEqual(custom_score.player, player)
        self.assertEqual(custom_score.chart, chart)
        self.assertEqual(custom_score.score, 990000)
        self.assertEqual(custom_score.normalized, -5.2)

    def test_create_chart_pair_defaults_and_overrides(self):
        pair = create_chart_pair()
        self.assertIsNotNone(pair.x_chart)
        self.assertIsNotNone(pair.y_chart)
        self.assertNotEqual(pair.x_chart.id, pair.y_chart.id)
        self.assertEqual(pair.slope, 1.0)
        self.assertEqual(pair.strength, 1.0)

        chart1 = create_chart()
        chart2 = create_chart()
        custom_pair = create_chart_pair(
            x_chart=chart1,
            y_chart=chart2,
            slope=1.25,
            strength=5.0,
        )
        self.assertEqual(custom_pair.x_chart, chart1)
        self.assertEqual(custom_pair.y_chart, chart2)
        self.assertEqual(custom_pair.slope, 1.25)
        self.assertEqual(custom_pair.strength, 5.0)

    def test_helpers_never_create_base_data_rows(self):
        base_data_models = [
            Difficulty,
            Version,
            Region,
            Cabinet,
            CabinetModel,
            ProfileVisibility,
        ]
        initial_counts = {model: model.objects.count() for model in base_data_models}

        create_song()
        create_chart()
        create_song_lock()
        create_unlock_group()
        create_unlock_event()
        create_unlock_task()
        create_chart_unlock()
        create_user()
        create_user(with_django_user=True)
        create_user_score()
        create_user_unlock()
        create_player()
        create_score()
        create_chart_pair()

        for model in base_data_models:
            self.assertEqual(
                model.objects.count(),
                initial_counts[model],
                f"{model.__name__} count changed after calling helpers",
            )
