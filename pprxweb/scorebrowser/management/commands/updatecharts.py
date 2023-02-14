from django.core.management.base import BaseCommand, CommandError
from scorebrowser.models import *
import json
import requests


# song_ids that 3icecream doesn't report as deleted, but are definitely gone
DELETED_SONGS = [
	#'blDbDqdo1D0odlQd9biIoio8ioQPb80i',
]

class Command(BaseCommand):
	help = 'Use https://3icecream.com/js/songdata.js to refresh the songs and charts in the db'

	def handle(self, *args, **options):
		response = requests.get("https://3icecream.com/js/songdata.js")
		if response.status_code != 200:
			raise CommandError("Received {} response from songdata.js.\n\n{}".format(response.status_code, response.content))

		# TODO : this suffix is variable length now; find some method of doing this that parses the .js more properly
		prefix = b'var ALL_SONG_DATA='
		suffix = b';const EVENT_EXCLUSIONS=[30,40,50,60,70,80,90,110,120,130,140,150,170,180,200,210];const SONG_DATA_LAST_UPDATED_unixms=1676298786814;'

		for fetched_song in json.loads(response.content[len(prefix):-len(suffix)]):
			song = Song.objects.filter(id=fetched_song['song_id']).first()
			if song is None:
				song = Song(id=fetched_song['song_id'], version_id=fetched_song['version_num'], title=fetched_song['song_name'])
				print("Creating song {}".format(song.title))
			if (not song.removed) and (('deleted' in fetched_song) or (fetched_song['song_id'] in DELETED_SONGS)):
				print("Song {} is now removed".format(song.title))
				song.removed = True
			song.save()

			ratings = fetched_song['ratings'][:5]
			for difficulty, rating in enumerate(ratings):
				if rating <= 1:
					continue
				if (difficulty != 3) and (rating < 14) and (rating != max(ratings)):
					continue

				chart = Chart.objects.filter(song__id=song.id).filter(difficulty__id=difficulty).first()
				if chart is None:
					print("Creating chart {} -- {} -- {}".format(song.title, difficulty, rating))
					chart = Chart(song_id=song.id, difficulty_id=difficulty, rating=rating)
					chart.save()
				elif chart.rating != rating:
					print("Updating chart rating {} -- {} from {} to {}".format(song.title, difficulty, chart.rating, rating))
					chart.rating = rating
					chart.save()