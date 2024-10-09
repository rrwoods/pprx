from collections import OrderedDict
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User as DjangoUser
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from numpy import interp
from .forms import SetPasswordForm, UpdateEmailForm, UserRegistrationForm
from .misc import sort_key
from .models import *
from .tokens import ACCOUNT_ACTIVATION_TOKEN_GENERATOR
import json
import math
import requests
import time


def hello(request):
	return render(request, 'scorebrowser/hello.html')

def register(request):
	if request.user.is_authenticated:
		return redirect('/')

	if request.method == 'POST':
		form = UserRegistrationForm(request.POST)
		if form.is_valid():
			django_user = form.save(commit=False)
			django_user.is_active = False
			django_user.save()
			if activate_email(request, django_user, form.cleaned_data.get('email')):
				return render(request, 'scorebrowser/check_your_email.html', {'message_type': 'an activation message'})
			else:
				return render(request, 'scorebrowser/activation_error.html', {
					'error_message': "Couldn't send email -- make sure you typed the address correctly."
				})

	return render(request, 'scorebrowser/register.html', {'form': UserRegistrationForm()})

def activate_email(request, django_user, email):
	message = render_to_string('scorebrowser/activate_account.html', {
		'username': django_user.username,
		'domain': get_current_site(request).domain,
		'uid': urlsafe_base64_encode(force_bytes(django_user.pk)),
		'token': ACCOUNT_ACTIVATION_TOKEN_GENERATOR.make_token(django_user),
		'protocol': 'https' if request.is_secure() else 'http',
	})

	email = EmailMessage('Activate your PPR X account', message, to=[email])
	return email.send()

def activate(request, uidb64, token):
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		django_user = DjangoUser.objects.get(pk=uid)

		if ACCOUNT_ACTIVATION_TOKEN_GENERATOR.check_token(django_user, token):
			django_user.is_active = True
			django_user.save()
			login(request, django_user)

			# if this activation was part of registration, they now need to link their sanbai
			# if this activation was post-registration, they probably already have done that
			if User.objects.filter(django_user=django_user).exists():
				return render(request, 'scorebrowser/loggedin.html')
			return redirect('link_sanbai')

	except:
		pass  # just fall through to error case below.

	return render(request, 'scorebrowser/activation_error.html', {
		'error_message': 'You clicked an invalid or expired activation link.'
	})

def login_user(request):
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			django_user = form.get_user()
			login(request, django_user)

			users = User.objects.filter(django_user=django_user)
			next_url = request.POST.get('next')
			return redirect(next_url or 'landing') if users else redirect('link_sanbai')
	else:
		form = AuthenticationForm(request)

	return render(request, 'scorebrowser/login.html', {'form': form})

@login_required(login_url='login')
def link_sanbai(request):
	return render(request, 'scorebrowser/link_sanbai.html', {'client_id': settings.CLIENT_ID})

def refresh_user(user, redirect_uri):
	refresh_response = requests.post('https://3icecream.com/oauth/token', data={
		'client_id': settings.CLIENT_ID,
		'client_secret': settings.CLIENT_SECRET,
		'grant_type': 'refresh_token',
		'refresh_token': user.refresh_token,
		'redirect_uri': redirect_uri,
	})
	response_json = refresh_response.json()
	user.access_token = response_json['access_token']
	user.refresh_token = response_json['refresh_token']
	user.save()

def finish_link(request):
	if 'code' not in request.GET:
		return HttpResponse("Couldn't log in, unknown error :/")
	player_id = request.GET.get('player_id')
	user = User.objects.filter(player_id=player_id).first()
	if user is None:
		user = User(player_id=player_id)
	user.django_user = request.user
	user.save()

	auth_response = requests.post('https://3icecream.com/oauth/token', data={
		'client_id': settings.CLIENT_ID,
		'client_secret': settings.CLIENT_SECRET,
		'grant_type': 'authorization_code',
		'code': request.GET.get('code'),
		'redirect_uri': request.build_absolute_uri(reverse('finish_link')),
	})
	if auth_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream auth token request; can't proceed.  3icecream error follows.<hr />{}".format(auth_response.status_code, auth_response.text))

	response_json = auth_response.json()
	user.access_token = response_json['access_token']
	user.refresh_token = response_json['refresh_token']
	user.save()

	hook_response = register_webhook(user)
	if hook_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream webhook registration; can't proceed.  3icecream error follows.<hr />{}".format(hook_response.status_code, hook_response.text))
	user.webhooked = True
	user.save()

	return render(request, 'scorebrowser/loggedin.html')

def register_webhook(user):
	return requests.post('https://3icecream.com/oauth/add_webhook_relationship', data={
		'client_id': settings.CLIENT_ID,
		'client_secret': settings.CLIENT_SECRET,
		'webhook_id': settings.WEBHOOK_ID,
		'access_token': user.access_token,
	})

@login_required(login_url='login')
def update_email_form(request):
	if request.method == 'POST':
		form = UpdateEmailForm(request.POST, instance=request.user)
		if form.is_valid():
			django_user = form.save()
			if activate_email(request, django_user, form.cleaned_data.get('email')):
				return render(request, 'scorebrowser/check_your_email.html', {'message_type': 'a confirmation message'})
			else:
				return render(request, 'scorebrowser/update_email.html', {
					'form': UpdateEmailForm(),
					'message': "Couldn't send email -- make sure you typed your email correctly."
				})

	return render(request, 'scorebrowser/update_email.html', {'form': UpdateEmailForm()})

@login_required(login_url='login')
def update_password(request):
	django_user = request.user
	if request.method == 'POST':
		form = SetPasswordForm(django_user, request.POST)
		if form.is_valid():
			form.save()
			return redirect('login')

	return render(request, 'scorebrowser/set_password.html', {'form': SetPasswordForm(django_user)})

def reset_password(request):
	if request.method == 'POST':
		form = PasswordResetForm(request.POST)
		if form.is_valid():
			user_email = form.cleaned_data.get('email')
			django_user = DjangoUser.objects.filter(email=user_email).first()
			if django_user:
				message = render_to_string('scorebrowser/reset_password_email.html', {
					'username': django_user.username,
					'domain': get_current_site(request).domain,
					'uid': urlsafe_base64_encode(force_bytes(django_user.pk)),
					'token': ACCOUNT_ACTIVATION_TOKEN_GENERATOR.make_token(django_user),
					'protocol': 'https' if request.is_secure() else 'http',
				})

				email = EmailMessage('Reset your PPR X password', message, to=[user_email])
				if email.send():
					return render(request, 'scorebrowser/check_your_email.html', {'message_type': 'a password reset link'})

	return render(request, "scorebrowser/reset_password.html", {'form': PasswordResetForm()})

def finish_reset(request, uidb64, token):
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		django_user = DjangoUser.objects.get(pk=uid)

		if ACCOUNT_ACTIVATION_TOKEN_GENERATOR.check_token(django_user, token):
			if request.method == 'POST':
				form = SetPasswordForm(django_user, request.POST)
				if form.is_valid():
					form.save()
					return redirect('login')

			form = SetPasswordForm(django_user)
			return render(request, 'scorebrowser/set_password.html', {'form': form})
		else:
			return render(request, 'scorebrowser/activation_error.html', {
				'error_message': 'That reset link has been used already.'
			})

	except:
		return redirect("/")


@login_required(login_url='login')
def landing(request):
	return render(request, 'scorebrowser/loggedin.html')

def logout_user(request):
	logout(request)
	return redirect('login')

def get_user(request):
	if not request.user:
		return None
	users = User.objects.filter(django_user=request.user)
	if not users:
		return None
	return users[0]

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

def update_progressive_unlock(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	task_id = int(request.POST['taskId'])
	event_id = int(request.POST['eventId'])

	UserProgressiveUnlock.objects.filter(user=user, event_id=event_id).delete()
	if task_id != -1:
		UserProgressiveUnlock.objects.create(user=user, event_id=event_id, task_id=task_id).create()

	return HttpResponse("Updated progressive unlock status.")

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


@login_required(login_url='login')
def unlocks(request):
	user = get_user(request)
	if not user:
		return redirect('link_sanbai')

	if not request.user.email:
		return redirect('update_email')

	allGroups = UnlockGroup.objects.all().order_by('ordering')
	allEvents = UnlockEvent.objects.filter(group__isnull=False).select_related('version').order_by('ordering')
	allTasks = UnlockTask.objects.all().order_by('ordering')
	allUserUnlocks = UserUnlock.objects.filter(user=user)
	groups = {x.id: x.name for x in allGroups}
	versions = {}
	events = {}
	tasks = {}
	userUnlocks = []
	for event in allEvents:
		versions[event.version_id] = event.version.name
		if event.version_id not in events:
			events[event.version_id] = {}
		if event.group_id not in events[event.version_id]:
			events[event.version_id][event.group_id] = []
		events[event.version_id][event.group_id].append(event)
		eventTasks = [t for t in allTasks if t.event_id == event.id]
		tasks[event.id] = eventTasks
		for task in eventTasks:
			if any(u.task_id == task.id for u in allUserUnlocks):
				userUnlocks.append(task.id)

	progressive_tasks = [u.task_id for u in UserProgressiveUnlock.objects.filter(user=user)]
	userUnlocks.extend(progressive_tasks)

	ordered_events = OrderedDict()
	for version_id in versions:
		version_events = OrderedDict()
		for group in allGroups:
			if group.id in events[version_id]:
				version_events[group.id] = events[version_id][group.id]
		ordered_events[version_id] = version_events

	unlockData = {
		'versions': versions.items(),
		'groups': groups,
		'events': ordered_events,
		'tasks': tasks,
		'userUnlocks': userUnlocks,
		'selectedRegionId': user.region_id,
		'regions': Region.objects.all().order_by('id'),
		'romanized_titles': user.romanized_titles,
	}
	return render(request, 'scorebrowser/unlocks.html', unlockData)

def compute_goal(target_quality, chart):
	quality_breakpoints = json.loads(chart.quality_breakpoints)
	if (target_quality < quality_breakpoints[0]):
		return None
	if (target_quality > quality_breakpoints[-1]):
		return 1000000

	normalized_goal = interp(
		target_quality,
		quality_breakpoints,
		json.loads(chart.normscore_breakpoints),
	)
	return (int(-(2**(-normalized_goal))/10)*10) + 1000000

def set_goal(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	user.goal_score = requestBody['target_score']
	user.goal_chart_id = requestBody['chart_id']
	user.save()

	target_quality = interp(
		-math.log2(1000000 - user.goal_score) if user.goal_score < 999999 else -2.323,
		json.loads(user.goal_chart.normscore_breakpoints),
		json.loads(user.goal_chart.quality_breakpoints),
	)
	response = {chart.id: compute_goal(target_quality, chart) for chart in Chart.objects.exclude(quality_breakpoints='')}
	return JsonResponse(response)

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

def set_selected_rank(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	user.selected_rank = requestBody["rank"]
	user.save()

	return HttpResponse('Set selected rank.')		

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

def target_requirement(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)

	goal_id = requestBody["goal_id"]
	version_id = requestBody["version_id"]
	return JsonResponse({'targets': user_targets(user, version_id, add=goal_id)})

def untarget_requirement(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)

	goal_id = requestBody["goal_id"]
	version_id = requestBody["version_id"]
	return JsonResponse({'targets': user_targets(user, version_id, remove=goal_id)})

def user_targets(user, version_id, add = None, remove = None):
	current_explicit = set(t.goal_id for t in UserRequirementTarget.objects.filter(user=user, version_id=version_id))
	implications = settings.IMPLICATIONS if version_id > 18 else settings.IMPLICATIONS_A20PLUS

	all_targets = current_explicit.copy()
	if add:
		all_targets.add(add)

	implicit_targets = set()
	for goal_id in all_targets:
		implicit_targets.update(implications[goal_id])
	all_targets.update(implicit_targets)

	if remove:
		if remove in all_targets:
			all_targets.remove(remove)
		removals = set()
		for goal_id in all_targets:
			if remove in implications[goal_id]:
				removals.add(goal_id)
		all_targets -= removals

	implicit_targets = set()
	for goal_id in all_targets:
		implicit_targets.update(implications[goal_id])
	new_explicit = all_targets - implicit_targets

	UserRequirementTarget.objects.filter(user=user, version_id=version_id, goal_id__in=(current_explicit - new_explicit)).delete()
	for goal_id in new_explicit - current_explicit:
		UserRequirementTarget.objects.create(user=user, version_id=version_id, goal_id=goal_id)

	return list(all_targets)

# This view is called by the 3icecream on-update webhook
# see https://3icecream.com/dev/docs for full details
@csrf_exempt
def fetch_scores(request):
	print("Webhook: enter")
	body = request.body.decode('utf-8')
	print("Webhook: decoded body")
	player_id = None
	for component in body.split('&'):
		[key, value] = component.split('=')
		if key == 'player_id':
			player_id = value
			break
	print("Webhook: Got player_id = {}".format(player_id))
	user = User.objects.get(player_id=player_id)
	print("Webhook: Got user")
	return perform_fetch(user, request.build_absolute_uri(reverse('scores')))

# This is for players for whom the webhook wasn't called for some reason
def force_fetch(request):
	user = get_user(request)
	return perform_fetch(user, request.build_absolute_uri(reverse('scores')))

def perform_fetch(user, redirect_uri):
	print("perform_fetch: enter")
	scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})
	if scores_response.status_code == 400:
		refresh_user(user, redirect_uri)
		scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})
	print("perform_fetch: got scores response")

	if scores_response.status_code != 200:
		return HttpResponse("Got {} from 3icecream; can't proceed.  3icecream error follows.<hr />{}".format(scores_response.status_code, scores_response.text))

	user.pulling_scores = True
	user.save()
	print("perform_fetch: pulling_scores set - username = {}".format(user.django_user.username))

	try:
		all_charts = {(chart.song_id, chart.difficulty_id): chart for chart in Chart.objects.all()}
		print("perform_fetch: got chart ids")
		all_song_ids = [song.id for song in Song.objects.all()]
		print("perform_fetch: got song ids")
		scores_lookup = {}
		for score in scores_response.json():
			difficulty = score['difficulty']
			if (difficulty > 4):
				continue

			song_id = score['song_id']
			title = score['song_name']
			timestamp = score['time_played'] or score['time_uploaded']
			lamp = score['lamp']
			score = score['score']

			key = (song_id, difficulty)
			scores_lookup[key] = (score, timestamp, lamp, title)

			if key not in all_charts:
				if song_id not in all_song_ids:
					Song.objects.create(id=song_id, version_id=20, title=title, sort_key=sort_key(title))

				# IMPORTANT!! updatecharts assumes that for hidden charts, rating = 0 -- update it if this changes!
				chart = Chart.objects.create(song_id=song_id, difficulty_id=difficulty, rating=0, hidden=True)
				all_charts[key] = chart
		print("perform_fetch: built scores dict")

		current_scores = {}
		for score in UserScore.objects.filter(user=user, current=True):
			current_scores[score.chart_id] = score
		print("perform_fetch: got current scores")

		formerly_current_scores = []
		new_scores = []

		for key in scores_lookup:
			chart = all_charts[key]
			normscore_breakpoints = json.loads(chart.normscore_breakpoints) if chart.normscore_breakpoints else None
			quality_breakpoints = json.loads(chart.quality_breakpoints) if chart.quality_breakpoints else None

			new_score = scores_lookup[key]
			normalized = (-2.323) if (new_score[0] == 1000000) else (-math.log2(1000000 - new_score[0]))
			quality = interp(normalized, normscore_breakpoints, quality_breakpoints) if quality_breakpoints else None
			new_entry = UserScore(
				user=user,
				chart_id=chart.id,
				score=new_score[0],
				normalized=normalized,
				timestamp=new_score[1],
				clear_type=new_score[2],
				quality=quality,
				current=True,
			)
			if chart.id in current_scores:
				old_score = current_scores[chart.id]
				if (new_score[0] > old_score.score) or (new_score[2] > old_score.clear_type):
					new_scores.append(new_entry)
					old_score.current = None
					formerly_current_scores.append(old_score)
			else:
				new_scores.append(new_entry)
		print("perform_fetch: built score updates")

		UserScore.objects.bulk_update(formerly_current_scores, ['current'])
		print("perform_fetch: cleared current on outdated scores")
		UserScore.objects.bulk_create(new_scores)
		print("perform_fetch: created new scores")
		return HttpResponse("Pulled new scores")

	finally:
		user.pulling_scores = False
		user.save()


def check_locks(song_id, song_locks, cabinet):
	if song_id in song_locks:
		for lock in song_locks[song_id]:
			version_match = (lock.version_id is None) or (lock.version_id == cabinet.version_id)
			region_match = (lock.region_id is None) or (lock.region_id == cabinet.region_id)
			model_match = (lock.model_id is None) or (lock.model_id == cabinet.model_id)
			if version_match and region_match and model_match:
				return True
	return False


@login_required(login_url='login')
def scores(request):
	#### USER RETRIEVAL ####

	redirect_uri = request.build_absolute_uri(reverse('scores'))
	user = get_user(request)
	if not user:
		return redirect('link_sanbai')
	if not user.webhooked:
		hook_response = register_webhook(user)
		if hook_response.status_code != 200:
			refresh_user(user, redirect_uri)
			hook_response = register_webhook(user)
			if hook_response.status_code != 200:
				return redirect('link_sanbai')
		user.webhooked = True
		user.save()

		perform_fetch(user, redirect_uri)

	if user.pulling_scores:
		while True:
			time.sleep(1)
			user = get_user(request)
			if not user.pulling_scores:
				break

	#### POST-CREATION EMAIL REGISTRATION ####
	# this is for users that signed up before I introduced email validation.
	if not request.user.email:
		return redirect('update_email')


	#### DB SCORE RETRIEVAL ####

	current_scores = {}
	score_db_query = UserScore.objects.filter(user=user, current=True)
	if (len(score_db_query) == 0):
		perform_fetch(user, redirect_uri)
		score_db_query = UserScore.objects.filter(user=user, current=True)
	for score in score_db_query:
		current_scores[score.chart_id] = score

	#### TARGET QUALITY COMPUTATION ####

	target_quality = None
	if user.goal_chart:
		goal_score = sorted([0, user.goal_score, 1000000])[1]
		normalized = -math.log2(1000000 - goal_score) if goal_score < 999999 else -2.323
		target_quality = interp(
			normalized,
			json.loads(user.goal_chart.normscore_breakpoints),
			json.loads(user.goal_chart.quality_breakpoints),
		)

	#### PER-USER CHART DATA RETRIEVAL ####

	aux = {entry.chart_id: entry for entry in UserChartAux.objects.filter(user_id=user.id)}

	#### UNLOCKS AND REGIONLOCK PROCESSING ####

	VISIBLE = 0
	EXTRA = 1
	LOCKED = 2
	UNAVAILABLE = 3

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
	for chart_unlock in ChartUnlock.objects.all().select_related("task__event", "task__event__group"):
		version_id = chart_unlock.task.event.version_id
		if version_id not in cab_versions:
			continue
		if chart_unlock.chart_id not in chart_unlocks[version_id]:
			chart_unlocks[version_id][chart_unlock.chart_id] = []
		chart_unlocks[version_id][chart_unlock.chart_id].append(chart_unlock)

	# set of task ids this user has completed
	user_unlocks = set(u.task_id for u in UserUnlock.objects.filter(user=user))

	for u in UserProgressiveUnlock.objects.filter(user=user).select_related("task__event"):
		# this is `set` update, not queryset.update -- just a local variable.
		user_unlocks.update(v.id for v in UnlockTask.objects.filter(event=u.task.event, ordering__lte=u.task.ordering))
	
	#### DATATABLE ENTRY GENERATION ####

	scores_data = []

	# {song_id: [ratings]}
	all_charts = {}

	chart_query = Chart.objects  \
		.select_related("song", "song__version", "difficulty")  \
		.filter(hidden=False)

	for chart in chart_query:
		entry = {}
		default_chart = True
		amethyst_required = True
		if chart.song.removed:
			default_chart = False
			amethyst_required = False
			entry["0"] = UNAVAILABLE
			entry["1"] = UNAVAILABLE
		else:
			for i, cabinet in enumerate(cabinets):
				cab_vis_id = str(i)
				if chart.song.version_id > cabinet.version_id:
					entry[cab_vis_id] = UNAVAILABLE
					default_chart = False
					amethyst_required = False
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
						if (not r.extra) and (not r.task.event.group):
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
		chart_rating = chart.rerate or chart.rating
		all_charts[chart.song_id][chart.difficulty_id] = chart_rating

		spice = chart.spice

		if chart.id in current_scores:
			db_score = current_scores[chart.id]
			score = db_score.score
			timestamp = db_score.timestamp
			clearType = db_score.clear_type
			quality = db_score.quality
		else:
			score = 0
			timestamp = 0
			clearType = 0
			quality = None

		if (clearType == 1) and (chart.id in aux) and (aux[chart.id].life4_clear):
			clearType = 2

		goal = None
		if (target_quality is not None) and (chart.quality_breakpoints):
			goal = compute_goal(target_quality, chart)

		entry['game_version'] = { 'id': chart.song.version_id, 'name': chart.song.version.name }
		entry['song_id'] = chart.song_id
		entry['song_name'] = { 'title': chart.song.title, 'sort_key': chart.song.sort_key }
		entry['alternate_title'] = chart.song.alternate_title
		entry['romanized_title'] = chart.song.romanized_title
		entry['searchable_title'] = chart.song.searchable_title
		entry['difficulty'] = { 'id': chart.difficulty_id, 'name': chart.difficulty.name, 'rating': chart_rating }
		entry['rating'] = chart_rating
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
		entry['removed'] = chart.song.removed
		entry['tracked'] = chart.tracked
		scores_data.append(entry)

	scores_data.sort(key=lambda x: x['quality'] or 0, reverse=True)
	for i, entry in enumerate(scores_data):
		entry['rank'] = i + 1

	life4_reqs = {
		'trials': {'best': user.best_trial, 'second': user.second_best_trial},
		'calories': user.best_calorie_burn,
		'consecutives': {2: user.best_two_consecutive, 3: user.best_three_consecutive},
	}

	requirement_targets = user_targets(user, white_cab.version_id)

	return render(request, 'scorebrowser/scores.html', {
		'scores': json.dumps(scores_data),
		'cabinets': cab_names,
		'versions': version_names,
		'white_version': white_cab.version_id,
		'all_charts': json.dumps(all_charts),
		'romanized_titles': user.romanized_titles,
		'life4_reqs': json.dumps(life4_reqs),
		'requirement_targets': json.dumps(requirement_targets),
		'selected_rank': user.selected_rank,
	})