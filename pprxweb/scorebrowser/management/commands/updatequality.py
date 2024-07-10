from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
import math


class Command(BaseCommand):
	help = 'Fill out quality ratings for all UserScores'

	def handle(self, *args, **options):
		updated_quality = []
		for score in UserScore.objects.all().select_related('chart'):
			if not score.chart.spice:
				continue
			score.quality = score.chart.spice - math.log2((1000001 - min(score.score, 999000))/1000000)
			updated_quality.append(score)
		UserScore.objects.bulk_update(updated_quality, ['quality'])