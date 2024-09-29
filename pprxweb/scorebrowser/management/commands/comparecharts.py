from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from scorebrowser.models import *
from scipy.odr import Model, Data, ODR
import math


def scale(parameters, data):
	return parameters[0] * data
scale_model = Model(scale)


class Command(BaseCommand):
	help = 'Compare each tracked chart to each other tracked chart within 1 level and assign a relative difficulty and confidence'

	def handle(self, *args, **options):
		public_scores = Score.objects.filter(score__gt=800000, score__lt=999000)
		player_scores = {}
		for entry in public_scores:
			if entry.player_id not in player_scores:
				player_scores[entry.player_id] = {}
			player_scores[entry.player_id][entry.chart_id] = entry.score

		tracked_chart_ids = {}
		for chart in Chart.objects.filter(tracked=True).filter(hidden=False):
			if chart.rating not in tracked_chart_ids:
				tracked_chart_ids[chart.rating] = []
			tracked_chart_ids[chart.rating].append(chart.id)

		unprocessed_pairs = []
		for level, chart_ids in tracked_chart_ids.items():
			for chart_id in chart_ids:
				for other_chart_id in chart_ids:
					if chart_id != other_chart_id:
						unprocessed_pairs.append((chart_id, other_chart_id))
				if (level + 1) in tracked_chart_ids:
					for other_chart_id in tracked_chart_ids[level + 1]:
						unprocessed_pairs.append((chart_id, other_chart_id))

		#unprocessed_pairs = list(UnprocessedPair.objects.all())
		remaining = len(unprocessed_pairs)
		skipped = 0
		print("Made {} pairs.  Clearing previous run's pairs...".format(remaining))

		ChartPair.objects.all().delete()
		new_pairs = []
		for unprocessed in unprocessed_pairs:
			score_pairs = []
			for (player_id, chart_scores) in player_scores.items():
				if (unprocessed[0] in chart_scores) and (unprocessed[1] in chart_scores):
					score_pairs.append((chart_scores[unprocessed[0]], chart_scores[unprocessed[1]]))

			remaining -= 1
			if (remaining % 1000) == 0:
				print(remaining)
			if len(score_pairs) < 10:
				skipped += 1
				continue

			x = []
			y = []
			w = []
			for pair in score_pairs:
				x.append(1000000 - pair[0])
				y.append(1000000 - pair[1])
				best = max(pair)
				# this is the best weighting I can think of right now:  exactly a AAA on the easier song
				# gets the most weight.  tail off to zero weight on either end of the score window.
				w.append((best - 800000)/190000 if best < 990000 else (999000 - best)/9000)

			data = Data(x, y, wd=w)
			odr = ODR(data, scale_model, beta0=[1.])
			out = odr.run()

			strength = len(score_pairs)*10000 / math.sqrt(out.res_var)
			new_pairs.append(ChartPair(x_chart_id=unprocessed[0], y_chart_id=unprocessed[1], slope=out.beta[0], strength=strength))
			new_pairs.append(ChartPair(x_chart_id=unprocessed[1], y_chart_id=unprocessed[0], slope=1/out.beta[0], strength=strength))

		print("{} skipped.".format(skipped))
		print("Writing to db...")
		batch_size = 1000
		i = int(len(new_pairs)/batch_size) * batch_size
		while i >= 0:
			print(i)
			ChartPair.objects.bulk_create(new_pairs[i:i+batch_size])
			i -= batch_size