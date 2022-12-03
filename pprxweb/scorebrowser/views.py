from django.conf import settings
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from .models import *
import json
import math
import requests

def landing(request):
	return render(request, 'scorebrowser/landing.html', {'client_id': settings.CLIENT_ID, 'fresh_user': 'player_id' not in request.session})

def charts(request):
	charts = Chart.objects.exclude(spice=None).order_by('-spice')
	return render(request, 'scorebrowser/charts.html', {'charts': charts})

def get_user(request):
	return User.objects.filter(player_id=request.session['player_id']).first()

def update_visibility(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	[song_id, cabinet, preference] = request.POST['preference'].split('-')
	posted_value = request.POST.get("pref_value", None)
	current_preference = SongVisibilityPreference.objects.filter(user__id=user.id).filter(song__id=song_id).first()
	if preference == 'hidec':
		if cabinet == 'white':
			current_preference.hide_challenge_white = (posted_value is not None)
		elif cabinet == 'gold':
			current_preference.hide_challenge_gold = (posted_value is not None)
	else:
		if cabinet == 'white':
			current_preference.white_visibility_id = posted_value
		elif cabinet == 'gold':
			current_preference.gold_visibility_id = posted_value
	current_preference.save()

	return HttpResponse("Preference saved.")

def create_default_visibility(user, song):
	return SongVisibilityPreference(
		user=user,
		song=song,
		hide_challenge_white=False,
		hide_challenge_gold=False,
		white_visibility_id=0,
		gold_visibility_id=0,
	)

def visibility(request):
	user = get_user(request)
	preferences = SongVisibilityPreference.objects.filter(user__id=user.id).all()
	visibility_names = [v.name for v in SongVisibility.objects.order_by('id')]

	preferences_dto = []
	for song in Song.objects.filter(removed=False).order_by('version_id', Lower('title')):
		preference = preferences.filter(song__id=song.id).first()
		if preference is None:
			preference = create_default_visibility(user, song)
			preference.save()
		preferences_dto.append(preference)
	return render(request, 'scorebrowser/visibility.html', {'preferences': preferences_dto, 'visibility_names': visibility_names})

def goals(request):
	user = get_user(request)
	benchmarks = Benchmark.objects.filter(rating__gte=13).order_by('chart__spice')
	return render(request, 'scorebrowser/goals.html', {'benchmarks': benchmarks, 'goal_score': user.goal_score, 'goal_benchmark': user.goal_benchmark_id})

def set_goal(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	benchmark_value = request.POST['benchmark_value']
	if request.POST['benchmark_type'] == 'score':
		try:
			user.goal_score = int(benchmark_value)
			if user.goal_benchmark == None:
				user.goal_benchmark = Benchmark.objects.order_by('chart__spice').first()
			user.save()
		except ValueError:
			pass
	else:
		user.goal_benchmark_id = int(benchmark_value)
		user.save()

	return HttpResponse('Set goal.')

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

	preferences = SongVisibilityPreference.objects.filter(user__id=user.id).all()
	target_quality = None
	if user.goal_benchmark:
		target_quality = user.goal_benchmark.chart.spice - math.log2((1000001 - user.goal_score)/1000000)

	scores_data = []
	scores_lookup = {'{}-{}'.format(score['song_id'], score['difficulty']): score['score'] for score in scores_response.json()}
	for chart in Chart.objects.filter(song__removed=False):
		visibility = preferences.filter(song__id=chart.song.id).first()
		if visibility is None:
			visibility = create_default_visibility(user, chart.song)

		white_visibility = visibility.white_visibility_id
		gold_visibility = visibility.gold_visibility_id
		if (chart.difficulty.id == 4):
			if visibility.hide_challenge_white:
				white_visibility = 2
			if visibility.hide_challenge_gold:
				gold_visibility = 2

		spice = round(chart.spice, 2) if chart.spice else None

		k = '{}-{}'.format(chart.song.id, chart.difficulty.id)
		score = scores_lookup[k] if k in scores_lookup else 0

		quality = None
		goal = None
		if spice is None:
			try:
				spice = round(Benchmark.objects.filter(description='easiest').filter(rating=chart.rating).first().chart.spice, 2)
				highest_spice = Benchmark.objects.filter(description='hardest').filter(rating=chart.rating).first().chart.spice
				goal = 1000001 - 15625*math.pow(2, 6 + highest_spice - target_quality) if target_quality else None
			except:
				print(chart.song.title)
		else:
			goal = 1000001 - 15625*math.pow(2, 6 + chart.spice - target_quality) if target_quality else None
			quality = round(chart.spice - math.log2((1000001 - score)/1000000), 2)
		goal = math.ceil(goal/10) * 10 if target_quality else None

		entry = {}
		entry['game_version'] = { 'id': chart.song.version.id, 'name': chart.song.version.name }
		entry['song_name'] = chart.song.title
		entry['difficulty'] = { 'id': chart.difficulty.id, 'name': chart.difficulty.name }
		entry['rating'] = chart.rating
		entry['spice'] = spice
		entry['score'] = score
		entry['quality'] = quality
		entry['goal'] = goal
		entry['white_visibility'] = white_visibility
		entry['gold_visibility'] = gold_visibility
		scores_data.append(entry)

	return render(request, 'scorebrowser/scores.html', {'scores': json.dumps(scores_data)})