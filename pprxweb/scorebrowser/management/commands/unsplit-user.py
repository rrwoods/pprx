from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *


class Command(BaseCommand):
	def handle(self, *args, **options):
		users = User.objects.filter(django_user__username="Temp-")
		if len(users) != 2:
			print(f'found {len(users)} users, aborting.')
			return

		ogUserId = min(u.id for u in users)
		ogUser = users.get(id=ogUserId)
		dupUsers = list(users.exclude(id=ogUserId))

		ogCurrentScores = list(UserScore.objects.filter(user_id=ogUserId, current=True))
		for dupUser in dupUsers:
			dupScores = UserScore.objects.filter(user=dupUser)
			scoresToMove = []
			for dupScore in dupScores:
				ogScore = [score for score in ogCurrentScores if score.chart_id == dupScore.chart_id]
				if not ogScore:
					print(f'No score to conflict with, moving {dupScore.id}')
					dupScore.user_id = ogUserId
					dupScore.save()
					continue

				ogScore = ogScore[0]
				if dupScore.current:
					if ogScore.timestamp > dupScore.timestamp:
						print(f'Duplicate current score found, un-duping dupe {dupScore.id}')
						dupScore.current = None
						dupScore.user_id = ogScore.user_id
						dupScore.save()
					else:
						print(f'Duplicate current score found, un-duping og {ogScore.id}')
						ogScore.current = None
						ogScore.save()
						dupScore.user_id = ogScore.user_id
						dupScore.save()
				else:
					print(f'Score {dupScore.id} is not current')
					dupScore.user_id = ogScore.user_id
					dupScore.save()

			ogUser.player_id = dupUser.player_id
			ogUser.access_token = dupUser.access_token
			ogUser.refresh_token = dupUser.refresh_token
			ogUser.save()

			dupUser.django_user_id = None
			dupUser.save()
			print(f"Stranded user object {dupUser.id}")