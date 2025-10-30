from django.test import SimpleTestCase
from unittest.mock import patch, MagicMock

from . import models


class ModelsSmokeTests(SimpleTestCase):
    def test_default_region_calls_region_get(self):
        dummy = MagicMock()
        dummy.id = 555
        with patch('pprxweb.scorebrowser.models.Region.objects.get', return_value=dummy) as mock_get:
            self.assertEqual(models.default_region(), 555)
            mock_get.assert_called_once()
