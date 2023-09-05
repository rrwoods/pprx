from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
from scipy.stats import gmean
import math


class Command(BaseCommand):
	help = "Recompute all songs' spice ratings using the current chart_pairs data"

	def handle(self, *args, **options):
		print("Building pairs dictionary...")
		pairs = {}
		for pair in ChartPair.objects.all():
			if pair.y_chart_id not in pairs:
				pairs[pair.y_chart_id] = []
			pairs[pair.y_chart_id].append(pair)

		current = {c.id: c.rating for c in Chart.objects.filter(tracked=True)}
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

		scale_factor = (2**anchor_value) / current[anchor_id]
		normalized = {chart_id: math.log2(raw*scale_factor) for chart_id, raw in current.items()}

		print("Applying upper-end spice fudge...")
		# the spice fudging is based on the Emerald V rankings in LIFE4 5.0, which has a requirement of 990k 16 floor
		# but, as i expect those thresholds would change if a harder chart came along, i want to do the same -- instantly
		# for this reason these are hand-selected; if an actually-harder one came along later i wouldn't want to pick it instead.
		# FUTURE RICK: and, in fact, this has happened: Lindwurm is harder than P20, but wasn't around when these were made :)
		hardest16id = Chart.objects.filter(song__title='New York EVOLVED (Type A)', difficulty_id=3).first().id
		hardest17id = Chart.objects.filter(song__title='Pluto The First', difficulty_id=3).first().id
		hardest18id = Chart.objects.filter(song__title='POSSESSION (20th Anniversary Mix)', difficulty_id=4).first().id
		hardest19id = Chart.objects.filter(song__title='Over The "Period"', difficulty_id=4).first().id
		# shush i know they are not 20s.
		hardest20id = Chart.objects.filter(song__title='ENDYMION', difficulty_id=4).first().id

		hardest16spice = normalized[hardest16id]
		hardest17spice = normalized[hardest17id]
		hardest18spice = normalized[hardest18id]
		hardest19spice = normalized[hardest19id]
		hardest20spice = normalized[hardest20id]

		target_quality = hardest16spice - math.log2((1000001 - 990000)/1000000)
		hardest17target = target_quality + math.log2((1000001 - 975000)/1000000)
		hardest18target = target_quality + math.log2((1000001 - 950000)/1000000)
		hardest19target = target_quality + math.log2((1000001 - 825000)/1000000)
		hardest20target = target_quality + math.log2((1000001 - 760000)/1000000)

		for chart_id in normalized:
			pre_fudge = normalized[chart_id]
			if pre_fudge <= hardest16spice:
				continue
			if pre_fudge >= hardest19spice:
				pre_range = (hardest19spice, hardest20spice)
				target_range = (hardest19target, hardest20target)
			elif pre_fudge >= hardest18spice:
				pre_range = (hardest18spice, hardest19spice)
				target_range = (hardest18target, hardest19target)
			elif pre_fudge >= hardest17spice:
				pre_range = (hardest17spice, hardest18spice)
				target_range = (hardest17target, hardest18target)
			else:
				pre_range = (hardest16spice, hardest17spice)
				target_range = (hardest16spice, hardest17target)
			into_range = (pre_fudge - pre_range[0]) / (pre_range[1] - pre_range[0])
			post_fudge = target_range[0] + (into_range*(target_range[1] - target_range[0]))
			normalized[chart_id] = post_fudge


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