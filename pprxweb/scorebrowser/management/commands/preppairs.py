from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *


class Command(BaseCommand):
	help = 'Determine which pairs of songs will be compared for spice computation'

	def handle(self, *args, **options):
		min_rating = 7
		max_rating = 19

		popular_charts = {min_rating-1: [], max_rating+1: []}
		unpopular_charts = {min_rating-1: [], max_rating+1: []}
		for rating in range(min_rating, max_rating + 1):
			charts = Chart.objects.filter(rating=rating, tracked=True)
			chart_popularity = []
			for chart in charts:
				# skip duplicate B4U Acyolyte -- it should have no scores against it
				# (score updater shunts all those scores over to the primary one)
				if chart.song.id == 'dll9D90dq1O09oObO66Pl8l9I9l0PbPP':
					continue
				qty = Score.objects.filter(chart__id=chart.id).count()
				chart_popularity.append((qty, chart.id))
			chart_popularity.sort(reverse=True)
			popular_charts[rating] = [p[1] for p in chart_popularity[:5]]
			unpopular_charts[rating] = [p[1] for p in chart_popularity[5:]]

		for rating in range(min_rating, max_rating + 1):
			print("handling {}".format(rating))
			for popular_chart in popular_charts[rating]:
				for chart in unpopular_charts[rating - 1]:
					UnprocessedPair.objects.create(x_chart_id=chart, y_chart_id=popular_chart)
				for chart in unpopular_charts[rating]:
					UnprocessedPair.objects.create(x_chart_id=chart, y_chart_id=popular_chart)
				for chart in unpopular_charts[rating + 1]:
					UnprocessedPair.objects.create(x_chart_id=chart, y_chart_id=popular_chart)
				for chart in popular_charts[rating]:
					if chart != popular_chart:
						UnprocessedPair.objects.create(x_chart_id=chart, y_chart_id=popular_chart)
				for chart in popular_charts[rating + 1]:
					UnprocessedPair.objects.create(x_chart_id=chart, y_chart_id=popular_chart)

		print(UnprocessedPair.objects.count())
		ChartPair.objects.all().delete()