from django.core.management.base import BaseCommand, CommandError
from scorebrowser.misc import sort_key
from scorebrowser.models import *
import json
import requests


class Command(BaseCommand):
	help = 'Use https://3icecream.com/js/songdata.js to refresh the songs and charts in the db'

	def handle(self, *args, **options):
		response = requests.get("https://3icecream.com/js/songdata.js")
		if response.status_code != 200:
			raise CommandError("Received {} response from songdata.js.\n\n{}".format(response.status_code, response.content))

		# TODO : this suffix is variable length now; find some method of doing this that parses the .js more properly
		# or, at the very least, look for the index of "[" for the beginning and ";const EVENT_EXCLUSIONS=[" for the end
		prefix = b'var ALL_SONG_DATA='
		suffix = b';const EVENT_EXCLUSIONS=[30,40,50,60,70,80,90,110,120,130,140,150,170,180,200,210,220,230,240,260,270,290,300];const SONG_DATA_LAST_UPDATED_unixms=1754722897432;'

		challenge_task = UnlockTask.objects.get(name="New Challenge charts (A3+)")
		for fetched_song in json.loads(response.content[len(prefix):-len(suffix)]):
			title = fetched_song['song_name'].replace("&amp;", "&")
			song = Song.objects.filter(id=fetched_song['song_id']).first()
			if song is None:
				song = Song(id=fetched_song['song_id'], version_id=fetched_song['version_num'], title=title)
				print("Creating song {}".format(song.title))
			if (not song.removed) and ('deleted' in fetched_song):
				print("Song {} is now removed".format(song.title))
				song.removed = True
			if (song.removed) and ('deleted' not in fetched_song):
				print("Song {} is now revived".format(song.title))
				song.removed = False
			if song.version_id != fetched_song['version_num']:
				song.version_id = fetched_song['version_num']
				print("Song {} moved to {}".format(song.title, song.version.name))
			if song.title != title:
				print("Song title {} corrected to {}".format(song.title, title))
				song.title = title

			for sanbai_k, db_k in [('alternate_name', 'alternate_title'), ('romanized_name', 'romanized_title'), ('searchable_name', 'searchable_title')]:
				v = fetched_song.get(sanbai_k, '')
				if v != getattr(song, db_k):
					setattr(song, db_k, v)
					print("Song {} has {} = {}".format(song.title, db_k, v))

					if db_k == 'searchable_title':
						song.sort_key = sort_key(v)

			song.save()

			ratings = fetched_song['ratings'][:5]
			for difficulty, rating in enumerate(ratings):
				if rating == 0:
					continue
				
				tracked = True
				if rating <= 1:
					tracked = False
				elif (difficulty != 3) and (rating < 14) and (rating != max(ratings)):
					tracked = False

				chart = Chart.objects.filter(song__id=song.id).filter(difficulty__id=difficulty).first()
				new_chart = False
				if chart is None:
					new_chart = True
					print("Creating {}chart {} -- {} -- {}".format(("" if tracked else "untracked "), song.title, difficulty, rating))
					chart = Chart(song_id=song.id, difficulty_id=difficulty, rating=rating, tracked=tracked)
					chart.save()
				elif chart.rating != rating:
					print("Updating chart rating {} -- {} from {} to {}".format(song.title, difficulty, chart.rating, rating))
					if chart.hidden:
						new_chart = True
					chart.rating = rating
					chart.tracked = tracked   # a 13->14 or 14->13 rerate might require this!
					chart.hidden = False
					chart.save()

				if new_chart and song.version_id <= 18:
					ChartUnlock.objects.create(task=challenge_task, chart=chart)