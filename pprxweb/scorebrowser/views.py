from django.conf import settings
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import *
import json
import math
import requests

def hello(request):
	return render(request, 'scorebrowser/hello.html')

def render_landing(request, fresh_user):
	if fresh_user:
		return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID})
	else:
		return render(request, 'scorebrowser/loggedin.html')

def landing(request):
	return render_landing(request, 'player_id' not in request.session)

def charts(request):
	charts = Chart.objects.exclude(spice=None).order_by('-spice')
	return render(request, 'scorebrowser/charts.html', {'charts': charts})

def get_user(request):
	if 'player_id' not in request.session:
		return None
	return User.objects.filter(player_id=request.session['player_id']).first()

def logged_in(request):
	if 'code' not in request.GET:
		return HttpResponse("Couldn't log in, unknown error :/")

	auth_response = requests.post('https://3icecream.com/oauth/token', data={
		'client_id': settings.CLIENT_ID,
		'client_secret': settings.CLIENT_SECRET,
		'grant_type': 'authorization_code',
		'code': request.GET.get('code'),
		'redirect_uri': request.build_absolute_uri(reverse('logged_in')),
	})
	if auth_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream; can't proceed.  3icecream error follows.<hr />{}".format(auth_response.status_code, auth_response.text))

	player_id = request.GET.get('player_id')
	request.session['player_id'] = player_id
	user = User.objects.filter(player_id=player_id).first()
	if user is None:
		user = User(player_id=player_id)
	response_json = auth_response.json()
	user.access_token = response_json['access_token']
	user.refresh_token = response_json['refresh_token']
	user.save()
	return render(request, 'scorebrowser/loggedin.html')

def set_region(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	selected_region_id = int(request.POST['region'])
	user.region_id = selected_region_id
	user.save()
	return HttpResponse("Updated region.")

def set_romanized_titles(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	posted_value = request.POST.get("pref_value", False)
	# this is not as insane as it looks, because htmx gives us "on" or False.
	user.romanized_titles = True if posted_value else False
	user.save()
	return HttpResponse("Romanized titles " + ("on" if posted_value else "off"))

def update_unlock(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	task_id = int(request.POST['taskId'])
	posted_value = request.POST.get("pref_value", None)
	if (posted_value):
		UserUnlock.objects.create(user=user, task_id=task_id)
	else:
		UserUnlock.objects.filter(user=user, task_id=task_id).delete()
	return HttpResponse("Updated unlock status.")

@csrf_exempt
def update_unlock_event(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	
	request_body = json.loads(request.body)
	event_id = request_body['event_id']
	unlock = request_body['unlock']

	user_unlocks = UserUnlock.objects.filter(user=user, task__event__id=event_id)
	if (unlock):
		already_unlocked = [u.task_id for u in user_unlocks]
		tasks = UnlockTask.objects.filter(event_id=event_id)
		for task in tasks:
			if task.id in already_unlocked:
				continue
			UserUnlock.objects.create(user=user, task=task)
	else:
		user_unlocks.delete()
	return HttpResponse("Updated unlock status.")


def unlocks(request):
	user = get_user(request)
	if not user:
		return render_landing(request, True)

	events = UnlockEvent.objects.filter(completable=True).order_by('ordering')
	allTasks = UnlockTask.objects.all().order_by('ordering')
	allUserUnlocks = UserUnlock.objects.filter(user=user)
	tasks = {}
	userUnlocks = []
	for event in events:
		eventTasks = [t for t in allTasks if t.event_id == event.id]
		tasks[event.id] = eventTasks
		for task in eventTasks:
			if any(u.task_id == task.id for u in allUserUnlocks):
				userUnlocks.append(task.id)
	unlockData = {
		'events': events,
		'tasks': tasks,
		'userUnlocks': userUnlocks,
		'selectedRegionId': user.region_id,
		'regions': Region.objects.all().order_by('id'),
		'romanized_titles': user.romanized_titles,
	}
	return render(request, 'scorebrowser/unlocks.html', unlockData)

@csrf_exempt
def set_goal(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	user.goal_score = requestBody['target_score']
	user.goal_chart_id = requestBody['chart_id']
	user.save()

	return HttpResponse('Set goal.')

@csrf_exempt
def set_chart_notes(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	chart_id = requestBody["chart_id"]
	notes = requestBody["notes"]

	UserChartAux.objects.update_or_create(
		user_id=user.id,
		chart_id=chart_id,
		defaults={'notes': notes},
	)

	return HttpResponse('Set chart notes.')

@csrf_exempt
def set_chart_bookmark(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	chart_id = requestBody["chart_id"]
	bookmark = requestBody["bookmark"]
	UserChartAux.objects.update_or_create(
		user_id=user.id,
		chart_id=chart_id,
		defaults={'bookmark': bookmark},
	)

	return HttpResponse('Set/cleared chart bookmark.')

@csrf_exempt
def set_chart_life4(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	chart_id = requestBody["chart_id"]
	life4_clear = requestBody["life4"]
	UserChartAux.objects.update_or_create(
		user_id=user.id,
		chart_id=chart_id,
		defaults={'life4_clear': life4_clear},
	)

	return HttpResponse('Set/cleared life4 clear.')	

@csrf_exempt
def set_trials(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	
	passed = requestBody["passed"]
	count = requestBody["count"]
	rank = requestBody["rank"]

	if passed:
		user.best_trial = max(user.best_trial, rank)
		if count > 1:
			user.second_best_trial = max(user.second_best_trial, rank)
	else:
		user.second_best_trial = min(user.second_best_trial, rank - 1)
		if count == 1:
			user.best_trial = min(user.best_trial, rank - 1)
	user.save()

	return JsonResponse({'best': user.best_trial, 'second': user.second_best_trial})

@csrf_exempt
def set_calories(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	
	calories = requestBody["calories"]
	passed = requestBody["passed"]

	if passed:
		user.best_calorie_burn = max(user.best_calorie_burn, calories)
	else:
		user.best_calorie_burn = min(user.best_calorie_burn, calories - 1)
	user.save()

	return JsonResponse({"calories": user.best_calorie_burn})

@csrf_exempt
def set_consecutives(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)

	passed = requestBody["passed"]
	count = requestBody["count"]
	level = requestBody["level"]

	if passed:
		user.best_two_consecutive = max(user.best_two_consecutive, level)
		if count > 2:
			user.best_three_consecutive = max(user.best_three_consecutive, level)
	else:
		user.best_three_consecutive = min(user.best_three_consecutive, level - 1)
		if count == 2:
			user.best_two_consecutive = min(user.best_two_consecutive, level - 1)
	user.save()

	return JsonResponse({2: user.best_two_consecutive, 3: user.best_three_consecutive})

def check_locks(song_id, song_locks, cabinet):
	if song_id in song_locks:
		for lock in song_locks[song_id]:
			version_match = (lock.version_id is None) or (lock.version_id == cabinet.version_id)
			region_match = (lock.region_id is None) or (lock.region_id == cabinet.region_id)
			model_match = (lock.model_id is None) or (lock.model_id == cabinet.model_id)
			if version_match and region_match and model_match:
				return True
	return False

# Produce a sorting key for a given title, such that datatables.js can use it to order titles like the game does.
# The key we produce is a string, but won't look anything like the actual title of the song; we just want it to
# be a list of keys that correspond to the characters of the string, where each key will be ordered based on
# where it falls in the final ordering scheme.  It's a string so that javascript compares it like a string.
# Knowing this, we convert each title to a list of numbers such that when strings of those numbers are compared,
# the corresponding titles are ordered the way we want.
# The 3icecream songdata.js "searchable_name" field is a pre-computed (THANK YOU Sunny!!) intermediary, where the japanese
# characters have been replaced by their hirigana equivalents, and strange characters have been unstrangeified (e.g. oversoul)
# So to produce our list of numbers for a final sort key, we need only convert each of the characters in the searchable_name
# to a number.
# Based on my experience with the game and looking through 3icecream's sorting code, I think the correct ordering is:
# - the vowel elongation character
# - japanese characters
# - letters
# - numbers
# Note that "symbols" does not appear here, because (I think) symbols should be normalized away by the searchable_title.
VOWEL_ELONGATION_CODE = 0x30FC
VOWEL_ELONGATION_KEY = ord('a') # start somewhere sane.

KATAKANA_CODE_LOWER = 0x30A1
KATAKANA_CODE_UPPER = 0x30F6
HIRIGANA_CODE_LOWER = 0x3041
HIRIGANA_CODE_UPPER = 0x3096
KATAKANA_HIRIGANA_CODE_OFFSET = KATAKANA_CODE_LOWER - HIRIGANA_CODE_LOWER
HIRIGANA_VOICED_CODES = [0x304C, 0x304E, 0x3050, 0x3052, 0x3054, 0x3056, 0x3058, 0x305A, 0x305C, 0x305E, 0x3060, 0x3062, 0x3065, 0x3067, 0x3069, 0x3070, 0x3073, 0x3076, 0x3079, 0x307C]
HIRIGANA_SEMI_VOICED_CODES = [0x3071, 0x3074, 0x3077, 0x307A, 0x307D]
HIRIGANA_SMALL_CODES = [0x3041, 0x3043, 0x3045, 0x3047, 0x3049, 0x3063, 0x3083, 0x3085, 0x3087, 0x308E, 0x3095, 0x3096]
JAPANESE_KEY = VOWEL_ELONGATION_KEY + 1

LOWERCASE_CODE_LOWER = ord('a')
LOWERCASE_CODE_UPPER = ord('z')
UPPERCASE_CODE_LOWER = ord('A')
UPPERCASE_CODE_UPPER = ord('Z')
LOWERCASE_UPPERCASE_CODE_OFFSET = LOWERCASE_CODE_LOWER - UPPERCASE_CODE_LOWER
ALPHABET_KEY = JAPANESE_KEY + (HIRIGANA_CODE_UPPER - HIRIGANA_CODE_LOWER) + 2

DIGIT_CODE_LOWER = ord('0')
DIGIT_CODE_UPPER = ord('9')
DIGIT_KEY = ALPHABET_KEY + 27

def sort_key(searchable_title):
	ret = ''
	for character in searchable_title:
		char_code = ord(character)
		
		if (char_code == VOWEL_ELONGATION_CODE):
			ret += (chr(VOWEL_ELONGATION_KEY))
			continue

		if (KATAKANA_CODE_LOWER <= char_code <= KATAKANA_CODE_UPPER):
			char_code -= KATAKANA_HIRIGANA_CODE_OFFSET
		if (HIRIGANA_CODE_LOWER <= char_code <= HIRIGANA_CODE_UPPER):
			if char_code in HIRIGANA_VOICED_CODES:
				char_code -= 1
			elif char_code in HIRIGANA_SEMI_VOICED_CODES:
				char_code -= 2
			elif char_code in HIRIGANA_SMALL_CODES:
				char_code += 1
			ret += (chr(char_code - HIRIGANA_CODE_LOWER + JAPANESE_KEY))
			continue

		if (LOWERCASE_CODE_LOWER <= char_code <= LOWERCASE_CODE_UPPER):
			char_code -= LOWERCASE_UPPERCASE_CODE_OFFSET
		if (UPPERCASE_CODE_LOWER <= char_code <= UPPERCASE_CODE_UPPER):
			ret += (chr(char_code - UPPERCASE_CODE_LOWER + ALPHABET_KEY))
			continue

		if (DIGIT_CODE_LOWER <= char_code <= DIGIT_CODE_UPPER):
			ret += (chr(char_code - DIGIT_CODE_LOWER + DIGIT_KEY))
		# everything else is ignored, including spaces.
	return ret


def scores(request):
	
	#### USER RETRIEVAL ####

	user = None
	if 'code' in request.GET:
		auth_response = requests.post('https://3icecream.com/oauth/token', data={
			'client_id': settings.CLIENT_ID,
			'client_secret': settings.CLIENT_SECRET,
			'grant_type': 'authorization_code',
			'code': request.GET.get('code'),
			'redirect_uri': request.build_absolute_uri(reverse('scores')),
		})
		if auth_response.status_code != 200:
			return HttpResponse("Got {} from 3icecream; can't proceed.  3icecream error follows.<hr />{}".format(auth_response.status_code, auth_response.text))

		player_id = request.GET.get('player_id')
		request.session['player_id'] = player_id
		user = User.objects.filter(player_id=player_id).first()
		if user is None:
			user = User(player_id=player_id)
		response_json = auth_response.json()
		user.access_token = response_json['access_token']
		user.refresh_token = response_json['refresh_token']
		user.save()
	else:
		user = get_user(request)

	if not user:
		return render_landing(request, True)

	#### 3ICECREAM SCORE RETRIEVAL ####

	scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})
	if scores_response.status_code == 400:
		if user.refresh_token is None:
			return render_landing(request, True)
		refresh_response = requests.post('https://3icecream.com/oauth/token', data={
			'client_id': settings.CLIENT_ID,
			'client_secret': settings.CLIENT_SECRET,
			'grant_type': 'refresh_token',
			'refresh_token': user.refresh_token,
			'code': request.GET.get('code'),
			'redirect_uri': request.build_absolute_uri(reverse('scores')),
		})
		if refresh_response.status_code != 200:
			return render_landing(request, True)
		response_json = refresh_response.json()
		user.access_token = response_json['access_token']
		user.refresh_token = response_json['refresh_token']
		user.save()

		scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})

	if scores_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream; can't proceed.  3icecream error follows.<hr />{}".format(scores_response.status_code, scores_response.text))

	#### TARGET QUALITY COMPUTATION ####

	target_quality = None
	if user.goal_chart:
		goal_score = sorted([0, user.goal_score, 999000])[1]
		target_quality = user.goal_chart.spice - math.log2((1000001 - goal_score)/1000000)

	#### PER-USER CHART DATA RETRIEVAL ####

	aux = {entry.chart_id: entry for entry in UserChartAux.objects.filter(user_id=user.id)}

	#### UNLOCKS AND REGIONLOCK PROCESSING ####

	VISIBLE = 0
	EXTRA = 1
	LOCKED = 2
	UNAVAILABLE = 3

	scores_data = []
	# {'songid-difficulty': (score, timestamp, combo type)}
	scores_lookup = {}
	duplicate_song_ids = ['01lbO69qQiP691ll6DIiqPbIdd9O806o', 'dll9D90dq1O09oObO66Pl8l9I9l0PbPP']
	for score in scores_response.json():
		song_id = score['song_id']
		difficulty = score['difficulty']
		timestamp = score['time_played'] or score['time_uploaded']
		lamp = score['lamp']
		score = score['score']
		if song_id in duplicate_song_ids:
			song_id = duplicate_song_ids[0]
		key = '{}-{}'.format(song_id, difficulty)
		if (key in scores_lookup) and (scores_lookup[key][0] >= score):
			continue
		scores_lookup[key] = (score, timestamp, lamp)

	song_locks = {}
	for lock in SongLock.objects.all():
		if lock.song_id not in song_locks:
			song_locks[lock.song_id] = []
		song_locks[lock.song_id].append(lock)

	version_names = [{'id': v.id, 'name': v.name} for v in Version.objects.all().order_by('id')]
	cab_names = [
		{'id': 0, 'name': 'White'},
		{'id': 1, 'name': 'Gold'},
		{'id': 2, 'name': 'Gold only'},
	]

	all_cabinets = Cabinet.objects.all()
	[white_cab] = [c for c in all_cabinets if (not c.gold and c.region_id == user.region_id)]
	[gold_cab] = [c for c in all_cabinets if c.gold]
	cabinets = [white_cab, gold_cab]
	cab_versions = set(c.version_id for c in cabinets)

	# {version id: {chart id: [requirements]}}
	chart_unlocks = {v: {} for v in cab_versions}
	for chart_unlock in ChartUnlock.objects.all().select_related("task__event"):
		if chart_unlock.version_id not in cab_versions:
			continue
		if chart_unlock.chart_id not in chart_unlocks[chart_unlock.version_id]:
			chart_unlocks[chart_unlock.version_id][chart_unlock.chart_id] = []
		chart_unlocks[chart_unlock.version_id][chart_unlock.chart_id].append(chart_unlock)

	# set of task ids this user has completed
	user_unlocks = set(u.task_id for u in UserUnlock.objects.filter(user=user))
	
	#### DATATABLE ENTRY GENERATION ####

	# {song_id: [ratings]}
	all_charts = {}

	chart_query = Chart.objects  \
		.filter(song__removed=False)  \
		.select_related("song", "song__version", "difficulty")

	scores_by_diff = {diff: [] for diff in range(14, 20)}

	for chart in chart_query:
		if chart.song_id in duplicate_song_ids[1:]:
			continue

		entry = {}
		default_chart = True
		amethyst_required = True
		for i, cabinet in enumerate(cabinets):
			cab_vis_id = str(i)
			if chart.song.version_id > cabinet.version_id:
				entry[cab_vis_id] = UNAVAILABLE
				continue

			if check_locks(chart.song_id, song_locks, cabinet):
				entry[cab_vis_id] = UNAVAILABLE
				default_chart = False
				amethyst_required = False
				continue
			
			chart_vis = VISIBLE
			if chart.id in chart_unlocks[cabinet.version_id]:
				requirements = chart_unlocks[cabinet.version_id][chart.id]
				for r in requirements:
					default_chart = False
					if not r.task.event.amethyst_required:
						amethyst_required = False
					if (not r.extra) and (not r.task.event.completable):
						chart_vis = UNAVAILABLE
						break
					if (r.task_id not in user_unlocks):
						chart_vis = max(chart_vis, (EXTRA if r.extra else LOCKED))
			entry[cab_vis_id] = chart_vis

		if entry["0"] <= entry["1"]:
			entry["2"] = UNAVAILABLE
		else:
			entry["2"] = entry["1"]

		if chart.song_id not in all_charts:
			all_charts[chart.song_id] = [-1, -1, -1, -1, -1]
		all_charts[chart.song_id][chart.difficulty_id] = chart.rating

		spice = chart.spice

		k = '{}-{}'.format(chart.song_id, chart.difficulty_id)
		score, timestamp, clearType = scores_lookup[k] if (k in scores_lookup) else (0, 0, 0)
		if (clearType == 1) and (chart.id in aux) and (aux[chart.id].life4_clear):
			clearType = 2

		if chart.rating >= 14:
			scores_by_diff[chart.rating].append(score)

		quality = None
		goal = None
		if spice is not None:
			goal = 1000001 - 15625*math.pow(2, 6 + chart.spice - target_quality) if target_quality else None
			if score > 0:
				quality = chart.spice - math.log2((1000001 - min(score, 999000))/1000000)
			goal = sorted((0, math.ceil(goal/10) * 10, 999000))[1] if target_quality else None

		entry['game_version'] = { 'id': chart.song.version_id, 'name': chart.song.version.name }
		entry['song_id'] = chart.song_id
		entry['song_name'] = { 'title': chart.song.title, 'sort_key': sort_key(chart.song.searchable_title or chart.song.title) }
		entry['alternate_title'] = chart.song.alternate_title
		entry['romanized_title'] = chart.song.romanized_title
		entry['searchable_title'] = chart.song.searchable_title
		entry['difficulty'] = { 'id': chart.difficulty_id, 'name': chart.difficulty.name, 'rating': chart.rating }
		entry['rating'] = chart.rating
		entry['spice'] = spice
		entry['score'] = score
		entry['clear_type'] = clearType
		entry['quality'] = quality
		entry['goal'] = goal
		entry['spiced'] = spice is not None
		entry['chart_id'] = chart.id
		entry['distance'] = (goal - score) if goal else 0
		entry['timestamp'] = timestamp
		entry['notes'] = aux[chart.id].notes if chart.id in aux else ''
		entry['bookmarked'] = aux[chart.id].bookmark if chart.id in aux else False
		entry['default_chart'] = default_chart
		entry['amethyst_required'] = amethyst_required
		scores_data.append(entry)

	scores_data.sort(key=lambda x: x['quality'] or 0, reverse=True)
	for i, entry in enumerate(scores_data):
		entry['rank'] = i + 1

	life4_reqs = {
		'trials': {'best': user.best_trial, 'second': user.second_best_trial},
		'calories': user.best_calorie_burn,
		'consecutives': {2: user.best_two_consecutive, 3: user.best_three_consecutive},
	}

	return render(request, 'scorebrowser/scores.html', {
		'scores': json.dumps(scores_data),
		'cabinets': cab_names,
		'versions': version_names,
		'rank_requirements': json.dumps(settings.RANK_REQUIREMENTS),
		'all_charts': json.dumps(all_charts),
		'romanized_titles': user.romanized_titles,
		'life4_reqs': json.dumps(life4_reqs),
	})