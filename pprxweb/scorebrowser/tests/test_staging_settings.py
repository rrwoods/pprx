from pathlib import Path
from unittest.mock import MagicMock, patch
import environ
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from pprxweb.settings import (
    DEFAULT_EMAIL_BACKEND,
    DEFAULT_PROD_CSRF_ORIGINS,
    DEFAULT_PROD_HOSTS,
    DEFAULT_WEBHOOK_ID,
    load_runtime_settings,
)
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.helpers import create_user
from scorebrowser.views import refresh_user


def _make_env(values):
    env = environ.Env()
    env.ENVIRON = dict(values)
    return env


class RuntimeSettingsTests(SimpleTestCase):
    def test_database_url_uses_backwards_compatible_prod_defaults(self):
        env = _make_env({
            'DJANGO_SECRET_KEY': 'secret',
            'CLIENT_ID': 'cid',
            'CLIENT_SECRET': 'csecret',
            'GOOGLE_USERNAME': 'mailer@example.com',
            'GOOGLE_APP_PASSWORD': 'app-password',
            'DATABASE_URL': 'mysql://produser:prodpass@db.example.com:25060/ebdb?ssl-mode=REQUIRED',
        })

        cfg = load_runtime_settings(env)

        self.assertEqual(cfg['ALLOWED_HOSTS'], DEFAULT_PROD_HOSTS)
        self.assertEqual(cfg['CSRF_TRUSTED_ORIGINS'], DEFAULT_PROD_CSRF_ORIGINS)
        self.assertEqual(cfg['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https'))
        self.assertFalse(cfg['DEBUG'])
        self.assertEqual(cfg['EMAIL_BACKEND'], DEFAULT_EMAIL_BACKEND)
        self.assertEqual(cfg['WEBHOOK_ID'], DEFAULT_WEBHOOK_ID)
        self.assertIsNone(cfg['SANBAI_OAUTH_REDIRECT_URI'])
        self.assertFalse(cfg['IS_STAGING'])
        self.assertEqual(cfg['DATABASES']['default']['ENGINE'], 'django.db.backends.mysql')
        self.assertEqual(cfg['DATABASES']['default']['NAME'], 'ebdb')
        self.assertNotIn('ssl-mode', cfg['DATABASES']['default']['OPTIONS'])
        self.assertNotIn('ssl', cfg['DATABASES']['default']['OPTIONS'])

    def test_staging_env_overrides_and_db_ca_cert(self):
        pem = '-----BEGIN CERTIFICATE-----\\nTESTCERTDATA\\n-----END CERTIFICATE-----'
        env = _make_env({
            'DJANGO_SECRET_KEY': 'staging-secret',
            'CLIENT_ID': 'cid',
            'CLIENT_SECRET': 'csecret',
            'DATABASE_URL': 'mysql://pprx_staging:pw@db.example.com:25060/pprx_staging?ssl-mode=REQUIRED',
            'DB_CA_CERT': pem,
            'ALLOWED_HOSTS': 'pprx-staging.ondigitalocean.app,staging.example.com',
            'CSRF_TRUSTED_ORIGINS': 'https://pprx-staging.ondigitalocean.app',
            'DEBUG': 'True',
            'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
            'WEBHOOK_ID': '',
            'SANBAI_OAUTH_REDIRECT_URI': 'https://pprx.gg/scorebrowser/scores',
            'IS_STAGING': 'True',
        })

        cfg = load_runtime_settings(env)

        self.assertEqual(cfg['ALLOWED_HOSTS'], ['pprx-staging.ondigitalocean.app', 'staging.example.com'])
        self.assertEqual(cfg['CSRF_TRUSTED_ORIGINS'], ['https://pprx-staging.ondigitalocean.app'])
        self.assertEqual(cfg['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https'))
        self.assertTrue(cfg['DEBUG'])
        self.assertEqual(cfg['EMAIL_BACKEND'], 'django.core.mail.backends.console.EmailBackend')
        self.assertEqual(cfg['EMAIL_HOST_USER'], '')
        self.assertEqual(cfg['EMAIL_HOST_PASSWORD'], '')
        self.assertEqual(cfg['WEBHOOK_ID'], '')
        self.assertEqual(cfg['SANBAI_OAUTH_REDIRECT_URI'], 'https://pprx.gg/scorebrowser/scores')
        self.assertTrue(cfg['IS_STAGING'])

        options = cfg['DATABASES']['default']['OPTIONS']
        self.assertNotIn('ssl-mode', options)
        ca_path = Path(options['ssl']['ca'])
        self.assertTrue(ca_path.exists())
        self.assertEqual(
            ca_path.read_text(encoding='utf-8'),
            '-----BEGIN CERTIFICATE-----\nTESTCERTDATA\n-----END CERTIFICATE-----',
        )

    def test_smtp_email_backend_still_requires_google_credentials(self):
        env = _make_env({
            'DJANGO_SECRET_KEY': 'secret',
            'CLIENT_ID': 'cid',
            'CLIENT_SECRET': 'csecret',
        })

        with self.assertRaises(ImproperlyConfigured):
            load_runtime_settings(env)

    def test_non_smtp_email_backend_skips_google_credentials_and_uses_sqlite_without_db_url(self):
        env = _make_env({
            'DJANGO_SECRET_KEY': 'ci-placeholder',
            'CLIENT_ID': 'ci-placeholder',
            'CLIENT_SECRET': 'ci-placeholder',
            'EMAIL_BACKEND': 'django.core.mail.backends.dummy.EmailBackend',
        })

        cfg = load_runtime_settings(env)

        self.assertEqual(cfg['EMAIL_BACKEND'], 'django.core.mail.backends.dummy.EmailBackend')
        self.assertEqual(cfg['EMAIL_HOST_USER'], '')
        self.assertEqual(cfg['EMAIL_HOST_PASSWORD'], '')
        self.assertEqual(cfg['DATABASES']['default']['ENGINE'], 'django.db.backends.sqlite3')


class StagingBannerTests(PPRXTestCase):
    def test_default_environment_renders_update_message_not_staging_banner(self):
        response = self.client.get(reverse('hello'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="update-message"')
        self.assertNotContains(response, 'class="staging-banner"')
        self.assertNotContains(response, 'STAGING ENVIRONMENT')

    @override_settings(
        IS_STAGING=True,
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        WEBHOOK_ID='',
        SANBAI_OAUTH_REDIRECT_URI='https://pprx.gg/scorebrowser/scores',
    )
    def test_staging_environment_replaces_update_message_with_staging_banner(self):
        response = self.client.get(reverse('hello'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="staging-banner"')
        self.assertContains(response, 'STAGING ENVIRONMENT')
        self.assertContains(response, 'django.core.mail.backends.console.EmailBackend')
        self.assertContains(response, 'WEBHOOK_ID')
        self.assertContains(response, 'https://pprx.gg/scorebrowser/scores')
        self.assertNotContains(response, 'class="update-message"')


class StagingWebhookAndOAuthGuardTests(PPRXTestCase):
    def _create_logged_in_user(self, *, webhooked=False, access_token=None, refresh_token=None):
        user = create_user(
            with_django_user=True,
            webhooked=webhooked,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        user.django_user.email = 'user@example.com'
        user.django_user.save()
        self.client.force_login(user.django_user)
        return user

    @override_settings(WEBHOOK_ID='')
    @patch('scorebrowser.views.perform_fetch')
    @patch('scorebrowser.views.register_webhook')
    def test_scores_skips_webhook_and_empty_fetch_for_scrubbed_user_when_webhook_disabled(
        self, mock_register_webhook, mock_perform_fetch
    ):
        user = self._create_logged_in_user(webhooked=False, access_token=None)

        response = self.client.get(reverse('scores', args=[user.id]))

        self.assertEqual(response.status_code, 200)
        mock_register_webhook.assert_not_called()
        mock_perform_fetch.assert_not_called()
        user.refresh_from_db()
        self.assertFalse(user.webhooked)

    @override_settings(WEBHOOK_ID='')
    @patch('scorebrowser.views.perform_fetch')
    @patch('scorebrowser.views.register_webhook')
    def test_scores_skips_webhook_but_fetches_empty_scores_when_access_token_present(
        self, mock_register_webhook, mock_perform_fetch
    ):
        user = self._create_logged_in_user(webhooked=False, access_token='live-token')

        response = self.client.get(reverse('scores', args=[user.id]))

        self.assertEqual(response.status_code, 200)
        mock_register_webhook.assert_not_called()
        mock_perform_fetch.assert_called_once()
        user.refresh_from_db()
        self.assertFalse(user.webhooked)

    @override_settings(WEBHOOK_ID='hook-123')
    @patch('scorebrowser.views.perform_fetch')
    @patch('scorebrowser.views.register_webhook')
    def test_scores_registers_webhook_when_webhook_id_set(
        self, mock_register_webhook, mock_perform_fetch
    ):
        mock_register_webhook.return_value = MagicMock(status_code=200)
        user = self._create_logged_in_user(webhooked=False, access_token='live-token')

        response = self.client.get(reverse('scores', args=[user.id]))

        self.assertEqual(response.status_code, 200)
        mock_register_webhook.assert_called_once()
        user.refresh_from_db()
        self.assertTrue(user.webhooked)
        self.assertEqual(mock_perform_fetch.call_count, 2)

    @override_settings(WEBHOOK_ID='')
    @patch('scorebrowser.views.register_webhook')
    @patch('scorebrowser.views.requests.post')
    def test_finish_link_skips_webhook_when_webhook_id_empty(
        self, mock_post, mock_register_webhook
    ):
        user = self._create_logged_in_user(webhooked=False)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'access_token': 'new-access', 'refresh_token': 'new-refresh'},
        )

        response = self.client.get(
            reverse('finish_link'),
            {'code': 'auth-code', 'player_id': user.player_id},
        )

        self.assertEqual(response.status_code, 200)
        mock_register_webhook.assert_not_called()
        user.refresh_from_db()
        self.assertFalse(user.webhooked)
        self.assertEqual(user.access_token, 'new-access')

    @override_settings(WEBHOOK_ID='hook-123')
    @patch('scorebrowser.views.register_webhook')
    @patch('scorebrowser.views.requests.post')
    def test_finish_link_registers_webhook_when_webhook_id_set(
        self, mock_post, mock_register_webhook
    ):
        user = self._create_logged_in_user(webhooked=False)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'access_token': 'new-access', 'refresh_token': 'new-refresh'},
        )
        mock_register_webhook.return_value = MagicMock(status_code=200)

        response = self.client.get(
            reverse('finish_link'),
            {'code': 'auth-code', 'player_id': user.player_id},
        )

        self.assertEqual(response.status_code, 200)
        mock_register_webhook.assert_called_once()
        user.refresh_from_db()
        self.assertTrue(user.webhooked)

    @patch('scorebrowser.views.requests.post')
    def test_refresh_user_uses_passed_redirect_uri_by_default(self, mock_post):
        user = create_user(with_django_user=True, refresh_token='old-refresh')
        mock_post.return_value = MagicMock(
            json=lambda: {'access_token': 'new-access', 'refresh_token': 'new-refresh'},
        )

        ok = refresh_user(user, 'https://example.test/scorebrowser/scores')

        self.assertTrue(ok)
        self.assertEqual(
            mock_post.call_args.kwargs['data']['redirect_uri'],
            'https://example.test/scorebrowser/scores',
        )

    @override_settings(SANBAI_OAUTH_REDIRECT_URI='https://pprx.gg/scorebrowser/scores')
    @patch('scorebrowser.views.requests.post')
    def test_refresh_user_honors_sanbai_oauth_redirect_uri_setting(self, mock_post):
        user = create_user(with_django_user=True, refresh_token='old-refresh')
        mock_post.return_value = MagicMock(
            json=lambda: {'access_token': 'new-access', 'refresh_token': 'new-refresh'},
        )

        ok = refresh_user(user, 'https://pprx-staging.ondigitalocean.app/scorebrowser/scores')

        self.assertTrue(ok)
        self.assertEqual(
            mock_post.call_args.kwargs['data']['redirect_uri'],
            'https://pprx.gg/scorebrowser/scores',
        )

    @override_settings(SANBAI_OAUTH_REDIRECT_URI='https://custom.example/scorebrowser/scores')
    @patch('scorebrowser.management.commands.fetch.perform_fetch')
    def test_fetch_command_honors_sanbai_oauth_redirect_uri(self, mock_perform_fetch):
        user = create_user(with_django_user=True)

        call_command('fetch', user.django_user.username)

        mock_perform_fetch.assert_called_once_with(user, 'https://custom.example/scorebrowser/scores')

    @override_settings(SANBAI_OAUTH_REDIRECT_URI=None)
    @patch('scorebrowser.management.commands.fetch.perform_fetch')
    def test_fetch_command_defaults_to_prod_redirect_uri(self, mock_perform_fetch):
        user = create_user(with_django_user=True)

        call_command('fetch', user.django_user.username)

        mock_perform_fetch.assert_called_once_with(user, 'https://pprx.gg/scorebrowser/scores')
