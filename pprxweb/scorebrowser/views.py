from django.conf import settings
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import *
import json
import math
import requests

def hello(request):
	return render(request, 'scorebrowser/hello.html')

def landing(request):
	return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': 'player_id' not in request.session})

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

def unlocks(request):
	user = get_user(request)
	if not user:
		return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': True})

	events = UnlockEvent.objects.all().filter(completable=True).order_by('ordering')
	tasks = {}
	userUnlocks = []
	for event in events:
		eventTasks = UnlockTask.objects.filter(event=event).order_by('ordering')
		tasks[event.id] = eventTasks
		for task in eventTasks:
			if len(UserUnlock.objects.filter(user=user, task=task)) > 0:
				userUnlocks.append(task.id)
	unlockData = {
		'events': events,
		'tasks': tasks,
		'userUnlocks': userUnlocks,
	}
	return render(request, 'scorebrowser/unlocks.html', unlockData)

@ensure_csrf_cookie
def goals(request):
	user = get_user(request)
	if not user:
		return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': True})

	target_quality = None
	if user.goal_chart:
		target_quality = user.goal_chart.spice - math.log2((1000001 - user.goal_score)/1000000)

	charts_data = []
	for chart in Chart.objects.filter(song__removed=False):
		if not chart.spice:
			continue

		if target_quality:
			goal = 1000001 - 15625*math.pow(2, 6 + chart.spice - target_quality) if target_quality else None

		entry = {}
		entry['chart_id'] = chart.id
		entry['game_version'] = { 'id': chart.song.version.id, 'name': chart.song.version.name }
		entry['song_name'] = chart.song.title
		entry['difficulty'] = { 'id': chart.difficulty.id, 'name': chart.difficulty.name }
		entry['rating'] = chart.rating
		entry['spice'] = chart.spice
		entry['goal'] = math.ceil(goal/10) * 10 if target_quality else None
		charts_data.append(entry)

	return render(request, 'scorebrowser/goals.html', {'charts': json.dumps(charts_data)})

@csrf_exempt
def set_goal(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	user.goal_score = requestBody['target_score']
	user.goal_chart_id = requestBody['chart_id']
	user.save()

	# benchmark_value = request.POST['benchmark_value']
	# if request.POST['benchmark_type'] == 'score':
	# 	try:
	# 		user.goal_score = int(benchmark_value)
	# 		if user.goal_benchmark == None:
	# 			user.goal_benchmark = Benchmark.objects.order_by('chart__spice').first()
	# 		user.save()
	# 	except ValueError:
	# 		pass
	# else:
	# 	user.goal_benchmark_id = int(benchmark_value)
	# 	user.save()

	return HttpResponse('Set goal.')

def check_locks(song_id, song_locks, cabinet):
	if song_id in song_locks:
		for lock in song_locks[song_id]:
			version_match = (lock.version is None) or (lock.version == cabinet.version)
			region_match = (lock.region is None) or (lock.region == cabinet.region)
			model_match = (lock.model is None) or (lock.model == cabinet.model)
			if version_match and region_match and model_match:
				return True
	return False

def scores(request):
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
		return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': True})

	scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})
	if scores_response.status_code == 400:
		if user.refresh_token is None:
			return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': True})
		refresh_response = requests.post('https://3icecream.com/oauth/token', data={
			'client_id': settings.CLIENT_ID,
			'client_secret': settings.CLIENT_SECRET,
			'grant_type': 'refresh_token',
			'refresh_token': user.refresh_token,
			'code': request.GET.get('code'),
			'redirect_uri': request.build_absolute_uri(reverse('scores')),
		})
		if refresh_response.status_code != 200:
			return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': True})
		response_json = refresh_response.json()
		user.access_token = response_json['access_token']
		user.refresh_token = response_json['refresh_token']
		user.save()

		scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})

	if scores_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream; can't proceed.  3icecream error follows.<hr />{}".format(scores_response.status_code, scores_response.text))

	target_quality = None
	if user.goal_chart:
		target_quality = user.goal_chart.spice - math.log2((1000001 - user.goal_score)/1000000)

	VISIBLE = 0
	EXTRA = 1
	HIDDEN = 2

	scores_data = []
	scores_lookup = {'{}-{}'.format(score['song_id'], score['difficulty']): score['score'] for score in scores_response.json()}

	song_locks = {}
	for lock in SongLock.objects.all():
		if lock.song.id not in song_locks:
			song_locks[lock.song.id] = []
		song_locks[lock.song.id].append(lock)

	cabinets = Cabinet.objects.all()
	cabinet_vis = {}
	cabinet_vis_target = 0
	cab_names = []
	cab_versions = set()
	for cabinet in cabinets:
		cabinet_vis[cabinet.id] = str(cabinet_vis_target)
		cab_names.append({'id': cabinet_vis_target, 'name': cabinet.name})
		cabinet_vis_target += 1
		cab_versions.add(cabinet.version.id)

	# {version id: {chart id: [requirements]}}
	chart_unlocks = {v: {} for v in cab_versions}
	for chart_unlock in ChartUnlock.objects.all():
		if chart_unlock.version.id not in cab_versions:
			continue
		if chart_unlock.chart.id not in chart_unlocks[chart_unlock.version.id]:
			chart_unlocks[chart_unlock.version.id][chart_unlock.chart.id] = []
		chart_unlocks[chart_unlock.version.id][chart_unlock.chart.id].append(chart_unlock)

	# set of task ids this user has completed
	user_unlocks = set(u.task.id for u in UserUnlock.objects.filter(user=user))
	
	default_spice = {b.chart.rating: b.chart.spice for b in Benchmark.objects.filter(description='easiest')}
	default_goals = {b.chart.rating: 1000001 - 15625*math.pow(2, 6 + b.chart.spice - target_quality) if target_quality else None for b in Benchmark.objects.filter(description='hardest')}

	for chart in Chart.objects.filter(song__removed=False):
		entry = {}
		for cabinet in cabinets:
			if chart.song.version.id > cabinet.version.id:
				entry[cabinet_vis[cabinet.id]] = HIDDEN
				continue

			if check_locks(chart.song.id, song_locks, cabinet):
				entry[cabinet_vis[cabinet.id]] = HIDDEN
				continue
			
			extra = False
			locked = False
			if chart.id in chart_unlocks[cabinet.version.id]:
				requirements = chart_unlocks[cabinet.version.id][chart.id]
				for r in requirements:
					extra = extra or r.extra
					locked = locked or (r.task.id not in user_unlocks)
			if not locked:
				entry[cabinet_vis[cabinet.id]] = VISIBLE
			elif extra:
				entry[cabinet_vis[cabinet.id]] = EXTRA
			else:
				entry[cabinet_vis[cabinet.id]] = HIDDEN

		spice = chart.spice

		k = '{}-{}'.format(chart.song.id, chart.difficulty.id)
		score = scores_lookup[k] if k in scores_lookup else 0

		quality = None
		goal = None
		if spice is None:
			try:
				spice = default_spice[chart.rating]
				goal = default_goals[chart.rating]
			except:
				print(chart.song.title)
		else:
			goal = 1000001 - 15625*math.pow(2, 6 + chart.spice - target_quality) if target_quality else None
			quality = chart.spice - math.log2((1000001 - min(score, 999000))/1000000)
		goal = sorted((0, math.ceil(goal/10) * 10, 999000))[1] if target_quality else None

		entry['game_version'] = { 'id': chart.song.version.id, 'name': chart.song.version.name }
		entry['song_name'] = chart.song.title
		entry['difficulty'] = { 'id': chart.difficulty.id, 'name': chart.difficulty.name, 'rating': chart.rating }
		entry['rating'] = chart.rating
		entry['spice'] = spice
		entry['score'] = score
		entry['quality'] = quality
		entry['goal'] = goal
		scores_data.append(entry)

	return render(request, 'scorebrowser/scores.html', {'scores': json.dumps(scores_data), 'cabinets': cab_names})