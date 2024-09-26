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
	help = 'Iterate through unprocessed_pairs and compare the indicated charts'

	def handle(self, *args, **options):
		public_scores = Score.objects.filter(score__gt=800000, score__lt=999000)
		player_scores = {}
		for entry in public_scores:
			if entry.player_id not in player_scores:
				player_scores[entry.player_id] = {}
			player_scores[entry.player_id][entry.chart_id] = entry.score

		unprocessed_pairs = list(UnprocessedPair.objects.all())
		remaining = len(unprocessed_pairs)
		skipped = 0

		for unprocessed in unprocessed_pairs:
			score_pairs = []
			for (player_id, chart_scores) in player_scores.items():
				if (unprocessed.x_chart_id in chart_scores) and (unprocessed.y_chart_id in chart_scores):
					score_pairs.append((chart_scores[unprocessed.x_chart_id], chart_scores[unprocessed.y_chart_id]))

			remaining -= 1
			if len(score_pairs) < 10:
				skipped += 1
				unprocessed.delete()
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
			with transaction.atomic():
				ChartPair.objects.create(x_chart_id=unprocessed.x_chart_id, y_chart_id=unprocessed.y_chart_id, slope=out.beta[0], strength=strength)
				ChartPair.objects.create(x_chart_id=unprocessed.y_chart_id, y_chart_id=unprocessed.x_chart_id, slope=1/out.beta[0], strength=strength)
				unprocessed.delete()

			print(remaining)

		print("{} skipped.".format(skipped))