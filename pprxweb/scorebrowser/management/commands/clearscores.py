from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from scorebrowser.models import *


class Command(BaseCommand):
	help = 'Remove stored public scores (NOT user scores!)'

	def handle(self, *args, **options):
		print("Clearing public scores...")
		Score.objects.all().delete()
		print("...Done.")
