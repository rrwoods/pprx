from django.test import SimpleTestCase
from unittest.mock import MagicMock

from .views import check_locks, compute_goal


class ViewsHelperTests(SimpleTestCase):
    def test_check_locks_matching_lock_returns_true(self):
        class Lock:
            def __init__(self, version_id=None, region_id=None, model_id=None):
                self.version_id = version_id
                self.region_id = region_id
                self.model_id = model_id

        # lock matches because all fields are None (wildcard)
        song_locks = { 's1': [Lock()] }
        cab = MagicMock()
        cab.version_id = 1
        cab.region_id = 2
        cab.model_id = 3
        assert check_locks('s1', song_locks, cab) is True

    def test_check_locks_non_matching_returns_false(self):
        class Lock:
            def __init__(self, version_id=None, region_id=None, model_id=None):
                self.version_id = version_id
                self.region_id = region_id
                self.model_id = model_id

        song_locks = { 's1': [Lock(version_id=99)] }
        cab = MagicMock()
        cab.version_id = 1
        cab.region_id = 2
        cab.model_id = 3
        assert check_locks('s1', song_locks, cab) is False

    def test_compute_goal_edge_cases(self):
        class Chart:
            def __init__(self, norm, qual):
                self.normscore_breakpoints = norm
                self.quality_breakpoints = qual

        # quality_breakpoints ascending [10,20,30]
        chart = Chart(norm='[0, 1, 2]', qual='[10, 20, 30]')
        # below first
        self.assertIsNone(compute_goal(5, chart))
        # above last
        self.assertEqual(compute_goal(40, chart), 1000000)
