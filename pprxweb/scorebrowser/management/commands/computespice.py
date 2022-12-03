from django.core.management.base import BaseCommand, CommandError
from math import log
from scorebrowser.models import *
from scipy.stats import gmean


class Command(BaseCommand):
	help = "Recompute all songs' spice ratings using the current chart_pairs data"

	def handle(self, *args, **options):
		print("Building pairs dictionary...")
		pairs = {}
		for pair in ChartPair.objects.all():
			if pair.y_chart_id not in pairs:
				pairs[pair.y_chart_id] = []
			pairs[pair.y_chart_id].append(pair)

		current = {c.id: c.rating for c in Chart.objects.all()}
		reps = 500
		for i in range(reps):
			print('{} iterations remaining'.format(reps-i))
			previous = current
			current = {}
			for chart_id, raw_spice in previous.items():
				if chart_id not in pairs:
					continue
				weights = [c.strength for c in pairs[chart_id] if c.x_chart_id in previous]
				if sum(weights) < 200:
					continue

				values = [c.slope * previous[c.x_chart_id] for c in pairs[chart_id] if c.x_chart_id in previous]
				current[chart_id] = gmean(values, weights=weights)
		
		anchor_value = 10.0
		anchor_id = Chart.objects.filter(song__title="MAX 300").filter(difficulty__id=3).first().id

		base = 1.55452
		scale_factor = (base**anchor_value) / current[anchor_id]
		normalized = {chart_id: log(raw*scale_factor, base) for chart_id, raw in current.items()}

		# it is possible for a previously-spiced chart to end up with no entry here.
		# this can happen if enough scores have improved to beyond the 999000 threshold such that there isn't sufficient data to re-spice the song.
		# we'd rather remove the old spice than leave it, since the new data may be normalized differently.
		print("Clearing existing spice...")
		Chart.objects.all().update(spice=None)

		print("Setting new spice...")
		bulk = []
		for chart_id, spice in normalized.items():
			chart = Chart.objects.get(id=chart_id)
			chart.spice = spice
			bulk.append(chart)
		Chart.objects.bulk_update(bulk, ['spice'])