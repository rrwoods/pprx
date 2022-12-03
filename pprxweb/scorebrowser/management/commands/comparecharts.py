from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from scorebrowser.models import *
from scipy.odr import Model, Data, ODR
import math


def scale(parameters, data):
	return parameters[0] * data
scale_model = Model(scale)

query = """
	select x.score as xscore, y.score as yscore
	from scores x, scores y
	where
		x.chart_id=%s and
		y.chart_id=%s and
		x.player_id=y.player_id and
		xscore<999000 and xscore>800000 and
		yscore<999000 and yscore>800000
"""

def report(start, done, remaining):
	current = datetime.now()
	each = (current - start) / done
	when = (each * remaining) + current
	print ("{} done, {} remaining; estimated completion at {}".format(done, remaining, when))

class Command(BaseCommand):
	help = 'Iterate through unprocessed_pairs and compare the indicated charts'

	def handle(self, *args, **options):
		cursor = connection.cursor()
		unprocessed_pairs = list(UnprocessedPair.objects.all())
		done = 0
		skipped = 0
		remaining = len(unprocessed_pairs)
		start = datetime.now()

		for unprocessed in unprocessed_pairs:
			print('comparing {} and {}'.format(unprocessed.x_chart.song.title, unprocessed.y_chart.song.title))
			cursor.execute(query, (unprocessed.x_chart_id, unprocessed.y_chart_id))
			scores = cursor.fetchall()
			print(scores)
			done += 1
			remaining -= 1
			if len(scores) < 10:
				skipped += 1
				report(start, done, remaining)
				unprocessed.delete()
				continue

			x = []
			y = []
			w = []
			for pair in scores:
				x.append(1000000 - pair[0])
				y.append(1000000 - pair[1])
				best = max(pair)
				# this is the best weighting I can think of right now:  exactly a AAA on the easier song
				# gets the most weight.  tail off to zero weight on either end of the score window.
				w.append((best - 800000)/190000 if best < 990000 else (999000 - best)/9000)

			data = Data(x, y, wd=w)
			odr = ODR(data, scale_model, beta0=[1.])
			out = odr.run()

			strength = len(scores)*10000 / math.sqrt(out.res_var)
			with transaction.atomic():
				ChartPair.objects.create(x_chart_id=unprocessed.x_chart_id, y_chart_id=unprocessed.y_chart_id, slope=out.beta[0], strength=strength)
				ChartPair.objects.create(x_chart_id=unprocessed.y_chart_id, y_chart_id=unprocessed.x_chart_id, slope=1/out.beta[0], strength=strength)
				unprocessed.delete()

			report(start, done, remaining)

		print("{} skipped.".format(skipped))