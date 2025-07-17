from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
from scorebrowser.views import perform_fetch


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('username', type=str)

	def handle(self, *args, **options):
		username = options['username']
		print("Fetching scores for username {}".format(username))

		user = User.objects.get(django_user__username=username)
		perform_fetch(user, 'https://pprx.gg/scorebrowser/scores')