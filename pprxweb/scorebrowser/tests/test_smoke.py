import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from django.conf import settings
from django.core import mail
from django.db import connection
from django.test import TestCase
import requests
from scorebrowser.tests.runner import NetworkBlockedError


class SmokeTests(TestCase):
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
