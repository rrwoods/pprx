from django.test import SimpleTestCase

from . import apps
from . import urls


class AppsUrlsTests(SimpleTestCase):
    def test_app_config_name(self):
        cfg = apps.ScorebrowserConfig()
        self.assertEqual(cfg.name, 'scorebrowser')

    def test_urlpatterns_contain_expected_names(self):
        names = set([p.name for p in urls.urlpatterns if p.name])
        # check a few key names exist
        for expected in ('landing', 'register', 'login', 'scores', 'hello'):
            self.assertIn(expected, names)
