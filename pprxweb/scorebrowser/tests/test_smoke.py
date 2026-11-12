from django.db import connection
from django.test import TestCase


class SmokeTests(TestCase):
    def test_default_database_is_in_memory_sqlite(self):
        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(connection.is_in_memory_db())
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA database_list")
            databases = {name: path for _, name, path in cursor.fetchall()}
        self.assertEqual(databases["main"], "")
