from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from scorebrowser.models import *


class Command(BaseCommand):
	help = 'Assign every public score a normalized value based on its distance from a perfect score'

	def handle(self, *args, **options):
		with connection.cursor() as cursor:
			print("Normalizing non-MFCs")
			cursor.execute('update scores set normalized = -log(2, 1000000 - score) where score < 1000000')

			print("Normalizing MFCs")
			# this value is 1.000 more than the normalized value for one perfect.
			cursor.execute('update scores set normalized = -2.322 where score = 1000000')