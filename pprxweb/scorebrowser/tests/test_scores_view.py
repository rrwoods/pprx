from datetime import timedelta
from unittest import mock
from django.contrib.auth.models import User as DjangoUser
from django.urls import reverse
from django.utils import timezone
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.helpers import create_chart, create_song, create_user, create_user_score


class ScoresViewTests(PPRXTestCase):
    def _create_user_with_score_and_get(self, synchronization_started_at, song_id, title, score, clear_type):
        django_user = DjangoUser.objects.create_user(
            username=f"dj_{DjangoUser.objects.count() + 1}",
            email="user@example.com",
        )
        user = create_user(
            django_user=django_user,
            webhooked=True,
            synchronization_started_at=synchronization_started_at,
        )
        song = create_song(id=song_id, title=title)
        chart = create_chart(song=song, rating=14)
        create_user_score(user=user, chart=chart, score=score, clear_type=clear_type, current=True)

        self.client.force_login(user.django_user)
        return self.client.get(reverse("scores", args=[user.id]))

    def test_scores_renders_immediately_with_banner_when_synchronization_in_progress(self):
        response = self._create_user_with_score_and_get(
            synchronization_started_at=timezone.now() - timedelta(minutes=2),
            song_id="song_in_progress",
            title="Banner Test Song",
            score=945670,
            clear_type=3,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="synchronization-in-progress"')
        self.assertContains(response, "Banner Test Song")
        self.assertContains(response, "945670")

    def test_scores_renders_without_banner_when_idle(self):
        response = self._create_user_with_score_and_get(
            synchronization_started_at=None,
            song_id="song_idle",
            title="Idle Test Song",
            score=910000,
            clear_type=2,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="synchronization-in-progress"')
        self.assertContains(response, "Idle Test Song")
        self.assertContains(response, "910000")

    def test_scores_renders_without_banner_when_claim_is_stale(self):
        response = self._create_user_with_score_and_get(
            synchronization_started_at=timezone.now() - timedelta(minutes=10, seconds=1),
            song_id="song_stale",
            title="Stale Test Song",
            score=980000,
            clear_type=4,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="synchronization-in-progress"')
        self.assertContains(response, "Stale Test Song")
        self.assertContains(response, "980000")


class ScoresViewVisibilityTests(PPRXTestCase):
    PRIVATE, ADMIN_ONLY, PUBLIC = 0, 1, 2

    def _create_user(self, visibility_id, is_staff=False, **kwargs):
        django_user = DjangoUser.objects.create_user(
            username=f"dj_{DjangoUser.objects.count() + 1}",
            email="user@example.com",
            is_staff=is_staff,
        )
        return create_user(django_user=django_user, visibility_id=visibility_id, **kwargs)

    def _view_scores(self, viewer, owner):
        self.client.force_login(viewer.django_user)
        return self.client.get(reverse("scores", args=[owner.id]))

    def test_private_profile_is_forbidden_to_other_users(self):
        viewer = self._create_user(self.PUBLIC, webhooked=True)
        owner = self._create_user(self.PRIVATE, webhooked=True)

        response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 403)

    def test_admin_only_profile_is_forbidden_to_non_staff_users(self):
        viewer = self._create_user(self.PUBLIC, webhooked=True)
        owner = self._create_user(self.ADMIN_ONLY, webhooked=True)

        response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 403)

    def test_staff_can_view_admin_only_profile(self):
        viewer = self._create_user(self.PRIVATE, is_staff=True, webhooked=True)
        owner = self._create_user(self.ADMIN_ONLY, webhooked=True)

        response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_view_private_profile(self):
        viewer = self._create_user(self.PUBLIC, is_staff=True, webhooked=True)
        owner = self._create_user(self.PRIVATE, webhooked=True)

        response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 403)

    def test_public_profile_is_visible_to_other_users(self):
        viewer = self._create_user(self.PRIVATE, webhooked=True)
        owner = self._create_user(self.PUBLIC, webhooked=True)

        response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 200)

    def test_user_can_view_their_own_private_profile(self):
        user = self._create_user(self.PRIVATE, webhooked=True)

        response = self._view_scores(user, user)

        self.assertEqual(response.status_code, 200)

    def test_forbidden_request_does_not_touch_the_profile_owner(self):
        viewer = self._create_user(self.PUBLIC, webhooked=True)
        owner = self._create_user(self.PRIVATE, webhooked=False)

        with mock.patch("scorebrowser.views.register_webhook") as register_webhook, \
                mock.patch("scorebrowser.views.synchronize") as synchronize:
            response = self._view_scores(viewer, owner)

        self.assertEqual(response.status_code, 403)
        register_webhook.assert_not_called()
        synchronize.assert_not_called()
        owner.refresh_from_db()
        self.assertFalse(owner.webhooked)
