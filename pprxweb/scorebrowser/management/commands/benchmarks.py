from django.core.management.base import BaseCommand
from scorebrowser.models import *
import statistics

measures = {'easiest': min, 'median': statistics.median_low, 'hardest': max}

class Command(BaseCommand):
	help = 'Compute lowest, median, and highest spice per rating from 8 to 19'

	def handle(self, *args, **options):
		if Benchmark.objects.first() is None:
			print ("Initializing benchamrks...")
			for rating in range(8, 20):
				for description in measures:
					Benchmark(rating=rating, description=description).save()

		for benchmark in Benchmark.objects.all():
			spices = [chart.spice for chart in Chart.objects.filter(rating=benchmark.rating).filter(song__removed=False).exclude(spice=None)]
			chart = Chart.objects.filter(rating=benchmark.rating).filter(spice=measures[benchmark.description](spices)).first()

			benchmark.chart = chart
			benchmark.save()
			print ("{} {} = {} {} [{}]".format(benchmark.description, benchmark.rating, chart.song.title, chart.difficulty.name, chart.spice))