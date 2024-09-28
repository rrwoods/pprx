from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
from numpy import interp
import json


class Command(BaseCommand):
	help = 'Fill out quality ratings for all UserScores'

	def handle(self, *args, **options):
		updated_quality = []
		all_scores = UserScore.objects.all().select_related('chart')
		count = all_scores.count()
		batch_size = 1000
		for i in range(0, count, batch_size):
			print(count - i)
			batch = all_scores[i:i+batch_size]
			for score in batch:
				if not score.chart.spice:
					continue
				score.quality = interp(
					score.normalized,
					json.loads(score.chart.normscore_breakpoints),
					json.loads(score.chart.quality_breakpoints)
				)
			UserScore.objects.bulk_update(batch, ['quality'])