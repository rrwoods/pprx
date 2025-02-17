import csv
from django.core.management.base import BaseCommand, CommandError
import json
import math
import sys
from numpy import interp
from scorebrowser.models import *


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('score', type=int)
		parser.add_argument('level', type=int)

	def handle(self, *args, **options):
		score = options['score']
		level = options['level']
		print("Getting {}-point spice for all level {}s".format(score, level))

		charts = Chart.objects.filter(rating=level).exclude(spice=None).select_related('song', 'difficulty')
		normalized = -2.323 if (score == 1000000) else (-math.log2(1000000 - score))

		spices = [(c, interp(normalized, json.loads(c.normscore_breakpoints), json.loads(c.quality_breakpoints))) for c in charts]

		out = csv.writer(sys.stdout)
		for chart, spice in sorted(spices, key=lambda x: x[1]):
			out.writerow([spice, chart.song.title, chart.difficulty.name])