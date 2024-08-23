from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
import math


def report(start, done, remaining):
	current = datetime.now()
	each = (current - start) / done
	when = (each * remaining) + current
	print ("{} done, {} remaining; estimated completion at {}".format(done, remaining, when))


class Command(BaseCommand):
	help = 'Fill out quality ratings for all UserScores'

	def handle(self, *args, **options):
		updated_quality = []
		all_scores = UserScore.objects.all().select_related('chart')
		remaining = len(all_scores)
		done = 0
		start = datetime.now()

		for score in all_scores:
			done += 1
			remaining -= 1

			if not score.chart.spice:
				continue
			score.quality = score.chart.spice - math.log2((1000001 - min(score.score, 999000))/1000000)
			updated_quality.append(score)

			report(start, done, remaining)
		UserScore.objects.bulk_update(updated_quality, ['quality'])