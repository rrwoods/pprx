import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.core import mail
from django.db import connection
import requests
from scorebrowser.models import (
    Cabinet,
    CabinetModel,
    Chart,
    ChartUnlock,
    Difficulty,
    ProfileVisibility,
    Region,
    Song,
    SongLock,
    UnlockEvent,
    UnlockGroup,
    UnlockTask,
    User,
    Version,
)
from scorebrowser.tests import PPRXTestCase
from scorebrowser.tests.runner import NetworkBlockedError


class SmokeTests(PPRXTestCase):
    def test_catalog_tables_contain_only_a3_plus_exception(self):
        self.assertEqual(Song.objects.count(), 0)
        self.assertEqual(Chart.objects.count(), 0)
        self.assertEqual(SongLock.objects.count(), 0)
        self.assertEqual(UnlockGroup.objects.count(), 0)
        self.assertEqual(ChartUnlock.objects.count(), 0)

        self.assertEqual(UnlockEvent.objects.count(), 1)
        self.assertEqual(UnlockEvent.objects.first().name, "New Challenge charts (A3)")

        self.assertEqual(UnlockTask.objects.count(), 1)
        self.assertEqual(UnlockTask.objects.first().name, "New Challenge charts (A3+)")

    def test_user_created_with_required_fields_gets_defaults(self):
        user = User.objects.create(player_id="test_player_id")

        self.assertEqual(user.visibility.id, 0)
        self.assertEqual(user.visibility.name, "Private")

        default_region = Region.objects.get(user_default=True)
        self.assertEqual(user.region, default_region)
        self.assertTrue(user.region.user_default)

    def test_a3_plus_exception_exists_once_under_its_event(self):
        tasks = UnlockTask.objects.filter(name="New Challenge charts (A3+)")
        self.assertEqual(tasks.count(), 1)
        task = tasks.first()

        event = task.event
        self.assertEqual(event.name, "New Challenge charts (A3)")
        self.assertIsNone(event.group)

        current_version = Version.objects.order_by('id').last()
        self.assertEqual(event.version, current_version)

        events = UnlockEvent.objects.filter(name="New Challenge charts (A3)")
        self.assertEqual(events.count(), 1)
        self.assertEqual(list(event.unlocktask_set.all()), [task])

    def test_base_data_fixture_loaded_and_tables_contain_nothing_else(self):
        fixture_path = settings.BASE_DIR / 'scorebrowser' / 'fixtures' / 'basedata.json'
        with open(fixture_path, encoding='utf-8') as f:
            fixture_data = json.load(f)

        base_data_models = [
            Difficulty,
            Version,
            Region,
            Cabinet,
            CabinetModel,
            ProfileVisibility,
        ]

        fixture_counts = {model: 0 for model in base_data_models}
        for entry in fixture_data:
            model_cls = apps.get_model(entry['model'])
            self.assertIn(model_cls, base_data_models)
            fixture_counts[model_cls] += 1

            instance = model_cls.objects.get(pk=entry['pk'])
            for field_name, expected_value in entry['fields'].items():
                actual_value = getattr(instance, f"{field_name}_id", getattr(instance, field_name))
                self.assertEqual(actual_value, expected_value)

        for model_cls in base_data_models:
            self.assertEqual(
                model_cls.objects.count(),
                fixture_counts[model_cls],
                f"{model_cls.__name__} count does not match fixture count",
            )

    def test_settings_selects_custom_test_runner(self):
        self.assertEqual(settings.TEST_RUNNER, 'scorebrowser.tests.runner.PPRXTestRunner')

    def test_outbound_tcp_connection_is_blocked(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            with self.assertRaises(NetworkBlockedError):
                s.connect(('203.0.113.1', 80))

    def test_public_hostname_lookup_is_blocked(self):
        with self.assertRaises(NetworkBlockedError):
            socket.gethostbyname('example.com')

    def test_requests_https_call_is_blocked(self):
        with self.assertRaises(NetworkBlockedError):
            requests.get('https://example.com')

    def test_default_database_is_in_memory_sqlite(self):
        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(connection.is_in_memory_db())
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA database_list")
            databases = {name: path for _, name, path in cursor.fetchall()}
        self.assertEqual(databases["main"], "")

    def test_email_sent_during_tests_goes_to_outbox(self):
        mail.send_mail(
            "Test Subject",
            "Test body",
            "noreply@example.com",
            ["user@example.com"],
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")

    def test_runner_refuses_non_sqlite_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "throwaway_settings.py"
            settings_path.write_text(
                "from pprxweb.settings import *\n"
                "DATABASES = {\n"
                "    'default': {\n"
                "        'ENGINE': 'django.db.backends.mysql',\n"
                "        'NAME': 'pprx',\n"
                "        'USER': 'user',\n"
                "        'PASSWORD': 'password',\n"
                "        'HOST': '203.0.113.1',\n"
                "        'PORT': 3306,\n"
                "    }\n"
                "}\n"
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{temp_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
            proc = subprocess.run(
                [sys.executable, "manage.py", "test", "--settings=throwaway_settings"],
                cwd=str(settings.BASE_DIR),
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            output = proc.stdout + proc.stderr
            self.assertIn("django.db.backends.mysql", output)
            self.assertIn("only SQLite is supported", output)
