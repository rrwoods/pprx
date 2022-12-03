from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('x_chart_id', type=int)
		parser.add_argument('y_chart_id', type=int)

	def handle(self, *args, **options):
		print(options['x_chart_id'])
		print(options['y_chart_id'])

		x_chart = Chart.objects.get(id=options['x_chart_id'])
		y_chart = Chart.objects.get(id=options['y_chart_id'])

		rating = x_chart.rating + 1
		a_chart = x_chart
		final_slope = 1
		while rating < y_chart.rating:
			charts = Chart.objects.filter(rating=rating)
			chart_popularity = []
			for chart in charts:
				qty = Score.objects.filter(chart__id=chart.id).count()
				chart_popularity.append((qty, chart.id, chart))
			chart_popularity.sort(reverse=True)
			b_chart = chart_popularity[0][2]

			pair = ChartPair.objects.filter(x_chart__id=a_chart.id).filter(y_chart__id=b_chart.id).first()
			print('{} {} = {} * {} {}'.format(b_chart.song.title, b_chart.difficulty.name, pair.slope, a_chart.song.title, a_chart.difficulty.name))
			final_slope *= pair.slope

			a_chart = b_chart
			rating += 1

		pair = ChartPair.objects.filter(x_chart__id=a_chart.id).filter(y_chart__id=y_chart.id).first()
		print('{} {} = {} * {} {}'.format(y_chart.song.title, y_chart.difficulty.name, pair.slope, a_chart.song.title, a_chart.difficulty.name))
		final_slope *= pair.slope

		print('=====')
		print('{} {} = {} * {} {}'.format(y_chart.song.title, y_chart.difficulty.name, final_slope, x_chart.song.title, x_chart.difficulty.name))
