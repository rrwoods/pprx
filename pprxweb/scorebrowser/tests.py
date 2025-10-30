from django.test import SimpleTestCase

import matplotlib
matplotlib.use('Agg')  # use non-GUI backend for tests

from unittest.mock import patch

from . import misc, tokens, plots


class MiscSortKeyTests(SimpleTestCase):
	def test_vowel_elongation_maps_to_expected_char(self):
		# U+30FC should map to VOWEL_ELONGATION_KEY
		s = chr(misc.VOWEL_ELONGATION_CODE)
		self.assertEqual(misc.sort_key(s), chr(misc.VOWEL_ELONGATION_KEY))

	def test_case_insensitive_for_letters(self):
		self.assertEqual(misc.sort_key('a'), misc.sort_key('A'))

	def test_digits_map_into_digit_key_space(self):
		# '0' should map to the first digit key (DIGIT_KEY)
		self.assertEqual(misc.sort_key('0'), chr(misc.DIGIT_KEY))

	def test_space_and_symbols_ignored(self):
		self.assertEqual(misc.sort_key(' '), '')


class TokenGeneratorTests(SimpleTestCase):
	def test_make_hash_value_changes_with_is_active(self):
		class DummyUser:
			def __init__(self, pk, is_active):
				self.pk = pk
				self.is_active = is_active

		g = tokens.ACCOUNT_ACTIVATION_TOKEN_GENERATOR
		u1 = DummyUser(pk=42, is_active=False)
		v1 = g._make_hash_value(u1, 1000)
		u1.is_active = True
		v2 = g._make_hash_value(u1, 1000)
		self.assertNotEqual(v1, v2)


class PlotsTests(SimpleTestCase):
	def test_breakpoints_parses_json(self):
		class DummyChart:
			def __init__(self):
				self.normscore_breakpoints = '[1, 2, 3]'
				self.quality_breakpoints = '[4, 5, 6]'
				self.spice = 123

		chart = DummyChart()
		x, y = plots.breakpoints(chart)
		self.assertEqual(x, [1, 2, 3])
		self.assertEqual(y, [4, 5, 6])

	def test_plot_runs_without_showing_window(self):
		# Ensure plot() executes without raising; patch plt.show to avoid side-effects
		x = [0, 1, 2]
		y = [10, 20, 30]
		with patch('pprxweb.scorebrowser.plots.plt.show'):
			# should not raise
			plots.plot(x, y, spice=5)

