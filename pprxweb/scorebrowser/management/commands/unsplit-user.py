from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('username', type=str)

	def handle(self, *args, **options):
		username = options['username']
		print("Username:", username)
		users = User.objects.filter(django_user__username=username)
		if len(users) <= 2:
			print(f'Only found {len(users)} users, aborting.')
			return

		ogUserId = min(u.id for u in users)
		ogUser = users.get(id=ogUserId)
		dupUsers = list(users.exclude(id=ogUserId))

		ogCurrentScores = list(UserScore.objects.filter(user_id=ogUserId, current=True))
		for dupUser in dupUsers:
			dupScores = UserScore.objects.filter(user=dupUser)
			for dupScore in dupScores:
				if dupScore.current:
					ogScore = [score for score in ogCurrentScores if score.chart_id == dupScore.chart_id]
					if ogScore:
						ogScore = ogScore[0]
						if ogScore.timestamp > dupScore.timestamp:
							dupScore.current = False
							dupScore.user_id = ogScore.user_id
							dupScore.save()
						else:
							ogScore.current = False
							dupScore.user_id = ogScore.user_id
							dupScore.save()
				else:
					dupScore.user_id = ogScore.user_id
					dupScore.save()
			dupUser.django_user_id = None
			dupUser.save()
			print(f"Stranded user object {dupUser.id}")