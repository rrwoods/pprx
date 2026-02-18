from collections import OrderedDict
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User as DjangoUser
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Max
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
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
import re
import requests
import time
import traceback



DIFFICULTY_NAMES = ['Beginner', 'Basic', 'Difficult', 'Expert', 'Challenge']


def hello(request):
	return render(request, 'scorebrowser/hello.html')

def howto(request):
	return render(request, 'scorebrowser/howto.html')

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
	# this creates a bit of metaprogramming i'm not sure how to avoid --
	# whenever we add a new `@login_required` endpoint, it needs to be in this list.
	allowed_next = [
		'/scorebrowser/',
		'/scorebrowser/link_sanbai',
		'/scorebrowser/update_email_form',
		'/scorebrowser/update_password',
		'/scorebrowser/landing',
		'/scorebrowser/unlocks',
		'/scorebrowser/scores',
	]
	allowed_next_patterns = [
		'/scorebrowser/scores/\\d+',
	]
	if request.method == 'POST':
		print("login_user: getting filled authn form")
		form = AuthenticationForm(request, data=request.POST)
		print("login_user: checking form")
		if form.is_valid():
			print("login_user: form is valid, getting django user")
			django_user = form.get_user()
			print("login_user: got django user {}, logging in".format(django_user.username))
			login(request, django_user)

			print("login_user: logged in, getting PPR X user")
			users = User.objects.filter(django_user=django_user)
			print("login_user: got PPR X user, determining redirect")
			next_url = request.POST.get('next')
			print("login_user: attempting redirect to {}".format(next_url))
			if (not next_url) or ((next_url not in allowed_next) and (not any(re.match(re.compile(p), next_url) for p in allowed_next_patterns))):
				print("login_user: that redirect isn't allowed; going to landing instead")
				next_url = 'landing'
			print("login_user: performing redirect")
			return redirect(next_url) if users else redirect('link_sanbai')
	else:
		print("login_user: getting empty authn form")
		form = AuthenticationForm(request)

	print("login_user: presenting login.html")
	return render(request, 'scorebrowser/login.html', {'form': form})

@login_required(login_url='login')
def link_sanbai(request):
	return render(request, 'scorebrowser/link_sanbai.html', {'client_id': settings.CLIENT_ID})

def refresh_user(user, redirect_uri):
	print("refresh_user: enter")
	refresh_response = requests.post('https://3icecream.com/oauth/token', data={
		'client_id': settings.CLIENT_ID,
		'client_secret': settings.CLIENT_SECRET,
		'grant_type': 'refresh_token',
		'refresh_token': user.refresh_token,
		'redirect_uri': redirect_uri,
	})
	print("refresh_user: got token response from 3icecream")
	try:
		response_json = refresh_response.json()
		user.access_token = response_json['access_token']
		user.refresh_token = response_json['refresh_token']
		user.save()
	except:
		print("refresh_user: unexpected token response:")
		print(refresh_response.text)
		return False
	print("refresh_user: exit")
	return True

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
	user.reauth = False
	user.save()

	if not user.webhooked:
		hook_response = register_webhook(user)
		if hook_response.status_code != 200:
			print("Webhook registration error {}".format(hook_response.status_code))
			print(hook_response.text)
			return HttpResponse("Got {} from 3icecream webhook registration; can't proceed.  3icecream error follows.<hr />{}".format(hook_response.status_code, hook_response.text))
		user.webhooked = True
		user.save()

	return render(request, 'scorebrowser/loggedin.html')

def register_webhook(user):
	webhook_url = 'https://3icecream.com/oauth/add_webhook_relationship'
	print("Making webhook request to {}".format(webhook_url))
	print("client_id: [redacted]")
	print("client_secret: [redacted]")
	print("webhook_id: {}".format(settings.WEBHOOK_ID))
	print("access_token: {}".format(user.access_token))

	return requests.post(webhook_url, data={
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

	print("reset_password: Generating reset form")
	newResetForm = PasswordResetForm()
	print("reset_password: Rendering reset template")
	try:
		return render(request, "scorebrowser/reset_password.html", {'form': newResetForm})
	except Exception:
		print("----------")
		traceback.print_exc()
		print("----------")

def finish_reset(request, uidb64, token):
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		print("finish_reset: uid {}".format(uid))
		django_user = DjangoUser.objects.get(pk=uid)
		print("finish_reset: username {}".format(django_user.username))

		if ACCOUNT_ACTIVATION_TOKEN_GENERATOR.check_token(django_user, token):
			print("finish_reset: token valid")
			if request.method == 'POST':
				print("finish_reset: POST")
				form = SetPasswordForm(django_user, request.POST)
				if form.is_valid():
					print("finish_reset: form valid")
					form.save()
					print("finish_reset: saved")
					return redirect('login')

			print("finish_reset: GET (or invalid POST)")
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
	if users[0].reauth:
		return None
	return users[0]

def set_profile_visibility(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	selected_visibility_id = int(request.POST['visibility'])
	user.visibility_id = selected_visibility_id
	user.vis_asked = True
	user.save()
	return HttpResponse(ProfileVisibility.objects.get(id=selected_visibility_id).description)

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
		'selectedVisibilityId': user.visibility_id,
		'visibilities': ProfileVisibility.objects.all().order_by('id'),
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

def set_selected_flare(request):
	if request.method != 'POST':
		return

	user = get_user(request)
	requestBody = json.loads(request.body)
	user.selected_flare = requestBody["flare"]
	user.save()

	return HttpResponse('Set selected flare rank.')

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
	print("Webhook: Got user, username = {}".format(user.django_user.username))

	if user.last_fetch and ((timezone.now() - user.last_fetch).total_seconds() < 600):
		print("Webhook: Bailing on fetch due to webhook spam for this user.")
		return HttpResponse("Bailing on fetch due to webhook spam.")
	user.last_fetch = timezone.now()
	user.save()
	print("Webhook: Set last fetch time to now")
	return perform_fetch(user, request.build_absolute_uri(reverse('scores')))

# This is for players for whom the webhook wasn't called for some reason
def force_fetch(request):
	user = get_user(request)
	return perform_fetch(user, request.build_absolute_uri(reverse('scores')))

def perform_fetch(user, redirect_uri):
	print("perform_fetch: enter")
	scores_response = requests.post('https://3icecream.com/dev/api/v1/get_scores', data={'access_token': user.access_token})
	if scores_response.status_code == 400:
		print("perform_fetch: first get_scores failed. response:")
		print(scores_response.text)
		print("----------")
		print("perform_fetch: refreshing user and trying again")
		if not refresh_user(user, redirect_uri):
			print("perform_fetch: couldn't refresh; forcing re-auth - user must load scores page to re-link sanbai")
			user.reauth = True
			user.save()
			return HttpResponse('Need to re-link 3icecream!  Click "Browse Scores" above to do so.')

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

			rating = score['rating']
			song_id = score['song_id']
			title = score['song_name']
			timestamp = score['time_played'] or score['time_uploaded']
			lamp = score['lamp']
			flare_gauge = score['flare'] if 'flare' in score else None
			score = score['score']

			key = (song_id, difficulty)
			scores_lookup[key] = (score, timestamp, lamp, flare_gauge)

			if key not in all_charts:
				if song_id not in all_song_ids:
					Song.objects.create(id=song_id, version_id=20, title=title, sort_key=sort_key(title))
					all_song_ids.append(song_id)

				chart = Chart.objects.create(song_id=song_id, difficulty_id=difficulty, rating=rating, hidden=True)
				all_charts[key] = chart
		print("perform_fetch: built scores dict")

		current_scores = {}
		for score in UserScore.objects            \
				.filter(user=user, current=True)  \
				.only('score', 'clear_type', 'flare_gauge'):
			current_scores[score.chart_id] = score
		print("perform_fetch: got current scores")

		formerly_current_scores = []
		new_scores = []
		new_flares = []

		for key in scores_lookup:
			chart = all_charts[key]
			normscore_breakpoints = json.loads(chart.normscore_breakpoints) if chart.normscore_breakpoints else None
			quality_breakpoints = json.loads(chart.quality_breakpoints) if chart.quality_breakpoints else None

			new_score = scores_lookup[key]
			normalized = (-2.323) if (new_score[0] == 1000000) else (-math.log2(1000000 - new_score[0]))
			quality = None
			if (new_score[2] > 0) and quality_breakpoints:
				quality = interp(normalized, normscore_breakpoints, quality_breakpoints)
			new_entry = UserScore(
				user=user,
				chart_id=chart.id,
				score=new_score[0],
				normalized=normalized,
				timestamp=new_score[1],
				clear_type=new_score[2],
				flare_gauge=new_score[3],
				quality=quality,
				current=True,
			)
			if chart.id in current_scores:
				old_score = current_scores[chart.id]
				if (
					(new_score[0] > old_score.score) or
					(new_score[2] > old_score.clear_type) or
					(new_score[3] != old_score.flare_gauge)
				):
					new_scores.append(new_entry)
					old_score.current = None
					formerly_current_scores.append(old_score)
				elif (old_score.flare_gauge is None) and (new_score[3] is not None):
					old_score.flare_gauge = new_score[3]
					new_flares.append(old_score)
			else:
				new_scores.append(new_entry)
		print("perform_fetch: built score updates")

		UserScore.objects.bulk_update(formerly_current_scores, ['current'])
		print("perform_fetch: cleared current on outdated scores")
		UserScore.objects.bulk_create(new_scores)
		print("perform_fetch: created new scores")
		UserScore.objects.bulk_update(new_flares, ['flare_gauge'])
		print("perform_fetch: set flare gauges of old scores")
		return HttpResponse("Pulled new scores")

	except Exception:
		print("----------")
		traceback.print_exc()
		print("----------")

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
def my_scores(request):
	user = get_user(request)
	if not user:
		return redirect('link_sanbai')
	return redirect('scores/{}'.format(user.id))


def forbidden(request):
	return HttpResponse("You don't have permission to view this page.")


def admin(request):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	visible_users = User.objects.exclude(visibility_id=0)
	user_ids = {u.django_user.username: u.id for u in visible_users}
	return render(request, 'scorebrowser/admin.html', {
		'usernames': sorted(list(user_ids.keys()), key=lambda x: x.lower()),
		'user_ids': user_ids,
	})

def manage_unlocks(request):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	groups = UnlockGroup.objects.all()
	goldenLeague = {
		'group': groups.get(name="Golden League"),
		'newEvents': [],
		'newTasks': [],
		'deleteTasks': False,
	}
	grandPrix = {
		'group': groups.get(name="Grand Prix advance play"),
		'newEvents': [],
		'newTasks': [{'text': 'add GP pack', 'endpoint': 'add_gp_pack'}],
		'deleteTasks': True,
	}
	extraSavior = {
		'group': groups.get(name="Extra Savior"),
		'newEvents': [{'text': 'add Extra Savior folder', 'endpoint': 'add_extra_savior'}],
		'newTasks': [],
		'deleteTasks': False,
	}
	timeLimited = {
		'group': groups.get(name="Time-limited events"),
		'newEvents': [
			{'text': 'add event', 'endpoint': 'add_event'},
			{'text': 'add GALAXY BRAVE', 'endpoint': 'add_galaxy_brave'},
		],
		'newTasks': [{'text': 'add task', 'endpoint': 'add_task'}],
		'deleteTasks': False,
	}

	events = UnlockEvent.objects.filter(version_id=20)
	chartUnlocks = ChartUnlock.objects.all().select_related(
		'chart__song',
		'chart__difficulty',
	)

	unlockData = []
	for group in [goldenLeague, grandPrix, extraSavior, timeLimited]:
		groupData = {
			'newEvents': group['newEvents'],
			'newTasks': group['newTasks'],
			'deleteTasks': group['deleteTasks'],
			'id': group['group'].id,
			'name': group['group'].name,
			'events': [],
		}
		for event in events.filter(group=group['group']).order_by('ordering'):
			eventData = {
				'id': event.id,
				'name': event.name,
				'tasks': [],
			}
			for task in UnlockTask.objects.filter(event=event).order_by('ordering'):
				taskData = {
					'id': task.id,
					'name': task.name,
				}
				if group['deleteTasks']:
					taskSongs = {}
					for chartUnlock in chartUnlocks.filter(task=task):
						if chartUnlock.chart.song.title not in taskSongs:
							taskSongs[chartUnlock.chart.song.title] = []
						taskSongs[chartUnlock.chart.song.title].append(chartUnlock.chart.difficulty.id)
					taskSongData = ''
					for (title, difficulties) in sorted(taskSongs.items()):
						if len(difficulties) == 1:
							taskSongData += (title + ' ({})\n'.format(DIFFICULTY_NAMES[difficulties[0]]))
						else:
							taskSongData += (title + '\n')
					taskData['songs'] = taskSongData
				eventData['tasks'].append(taskData)
			groupData['events'].append(eventData)
		unlockData.append(groupData)
	
	return render(request, 'scorebrowser/manage_unlocks.html', {
		'unlockData': json.dumps(unlockData),
		'hiddenSongs': get_hidden_songs(),
	})


def get_hidden_songs():
	hiddenCharts = Chart.objects.filter(hidden=True).select_related('song')
	hiddenSongs = set(chart.song for chart in hiddenCharts)
	return sorted(list(hiddenSongs), key=lambda song: song.title.lower())


def delete_task(request, task_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	UnlockTask.objects.get(id=task_id).delete()
	return redirect('manage_unlocks')


def unlock_chart_collection(request, pageTitle, namePlaceholder):
	# {title: [bool for each difficulty]}
	hiddenCharts = {}
	for chart in Chart.objects.filter(hidden=True).select_related('song'):
		if chart.song.title not in hiddenCharts:
			hiddenCharts[chart.song.title] = [False, False, False, False, False, chart.song.title]
		hiddenCharts[chart.song.title][chart.difficulty_id] = chart.id

	return render(request, 'scorebrowser/unlock_chart_collection.html', {
		'pageTitle': pageTitle,
		'namePlaceholder': namePlaceholder,
		'eligibleCharts': [v for k, v in sorted(hiddenCharts.items(), key=lambda item: item[0].lower())]
	})


def create_task(request, event_id):
	task = UnlockTask.objects.create(
		event_id=event_id,
		name=request.POST['name'].strip(),
		ordering=UnlockTask.objects.aggregate(Max('ordering'))['ordering__max'] + 10,
	)
	for key in request.POST:
		if not key.isdigit():
			continue
		# no need to check the value;
		# in html forms, the key for a checkbox is absent if it's unchecked.
		
		chart = Chart.objects.get(id=int(key))
		chart.hidden = False
		chart.save()
		ChartUnlock.objects.create(task=task, chart=chart)
	return redirect('manage_unlocks')


def add_gp_pack(request, event_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		return create_task(request, event_id)

	return unlock_chart_collection(request, 'New GP pack', 'music pack vol.69')


def add_extra_savior(request, group_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		event = UnlockEvent.objects.create(
			version_id=20,
			group_id=group_id,
			name=request.POST['name'].strip(),
			ordering=UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10,
		)
		
		allCharts = Chart.objects.all().select_related('song', 'difficulty')
		selectedCharts = {}
		for key in request.POST:
			if not key.isdigit():
				continue

			chart = allCharts.get(id=int(key))
			chart.hidden = False
			chart.save()

			if chart.song.title not in selectedCharts:
				selectedCharts[chart.song.title] = [None, None, None, None, None]
			selectedCharts[chart.song.title][chart.difficulty.id] = chart

		ordering = 0
		for title, charts in sorted(selectedCharts, key=lambda item: item[0].lower()):
			for chart in charts:
				if chart is None:
					continue
				task = UnlockTask.objects.create(
					event=event,
					name='{} ({} {})'.format(title, chart.difficulty.name, chart.rating),
					ordering = ordering
				)
				ordering += 10

				ChartUnlock.objects.create(task=task, chart=chart, extra=True)

		return redirect('manage_unlocks')


	return unlock_chart_collection(request, 'New Extra Savior folder', 'folder name')


def add_galaxy_brave(request, group_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		event = UnlockEvent.objects.create(
			version_id=20,
			group_id=group_id,
			name='GALAXY BRAVE: {}'.format(request.POST['name'].upper().strip()),
			progressive=True,
			ordering=UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10,
		)
		ordering = 0
		for chart in Chart.objects.filter(song_id=request.POST['song']).select_related('difficulty').order_by('difficulty_id'):
			task = UnlockTask.objects.create(
				event=event,
				name='{} ({})'.format(chart.song.title, chart.difficulty.name),
				ordering=ordering,
			)
			ordering += 10
			ChartUnlock.objects.create(task=task, chart=chart)
			chart.hidden = False
			chart.save()
		return redirect('manage_unlocks')

	return render(request, 'scorebrowser/add_galaxy_brave.html', {'songs': get_hidden_songs()})


def add_event(request, group_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		UnlockEvent.objects.create(
			version_id=20,
			group_id=group_id,
			name=request.POST['name'].strip(),
			ordering=UnlockEvent.objects.aggregate(Max('ordering'))['ordering__max'] + 10,
		)
		return redirect('manage_unlocks')

	return render(request, 'scorebrowser/add_event.html')


def add_task(request, event_id):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		return create_task(request, event_id)

	event = UnlockEvent.objects.get(id=event_id)
	return unlock_chart_collection(request, 'New {} task'.format(event.name), 'task name')


def default_charts(request):
	user = get_user(request)
	if not user.django_user.is_staff:
		return redirect('forbidden')

	if request.method == 'POST':
		allCharts = Chart.objects.all().select_related('song', 'difficulty')
		selectedCharts = {}
		for key in request.POST:
			if not key.isdigit():
				continue

			chart = allCharts.get(id=int(key))
			chart.hidden = False
			chart.save()

		return redirect('manage_unlocks')

	return unlock_chart_collection(request, 'Mark default charts', 'type anything to confirm and hit enter')


@login_required(login_url='login')
def scores(request, user_id):
	#### USER RETRIEVAL ####
	user_id = int(user_id)
	scores_user = User.objects.get(id=user_id)

	redirect_uri = request.build_absolute_uri(reverse('scores'))
	logged_in_user = get_user(request)
	if not logged_in_user:
		return redirect('link_sanbai')
	if not scores_user.webhooked:
		hook_response = register_webhook(scores_user)
		if hook_response.status_code != 200:
			if not refresh_user(scores_user, redirect_uri):
				return redirect('link_sanbai')
			hook_response = register_webhook(scores_user)
			if hook_response.status_code != 200:
				return redirect('link_sanbai')
		scores_user.webhooked = True
		scores_user.save()

		perform_fetch(scores_user, redirect_uri)

	if user_id != logged_in_user.id:
		min_visibility = 2
		if logged_in_user.django_user.is_staff:
			min_visibility = 1
		if scores_user.visibility.id < min_visibility:
			return redirect('forbidden')

	if scores_user.pulling_scores:
		while True:
			time.sleep(1)
			scores_user = User.objects.get(id=user_id)
			if not scores_user.pulling_scores:
				break

	#### POST-CREATION EMAIL REGISTRATION ####
	# this is for users that signed up before I introduced email validation.
	if not request.user.email:
		return redirect('update_email')


	#### DB SCORE RETRIEVAL ####

	current_scores = {}
	score_db_query = UserScore.objects.filter(user=scores_user, current=True)
	if (len(score_db_query) == 0):
		perform_fetch(scores_user, redirect_uri)
		score_db_query = UserScore.objects.filter(user=scores_user, current=True)
	for score in score_db_query:
		current_scores[score.chart_id] = score

	#### TARGET QUALITY COMPUTATION ####

	target_quality = None
	if scores_user.goal_chart:
		goal_score = sorted([0, scores_user.goal_score, 1000000])[1]
		normalized = -math.log2(1000000 - goal_score) if goal_score < 999999 else -2.323
		target_quality = interp(
			normalized,
			json.loads(scores_user.goal_chart.normscore_breakpoints),
			json.loads(scores_user.goal_chart.quality_breakpoints),
		)

	#### PER-USER CHART DATA RETRIEVAL ####

	aux = {entry.chart_id: entry for entry in UserChartAux.objects.filter(user_id=scores_user.id)}

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
	[white_cab] = [c for c in all_cabinets if (not c.gold and c.region_id == scores_user.region_id)]
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
	user_unlocks = set(u.task_id for u in UserUnlock.objects.filter(user=scores_user))

	for u in UserProgressiveUnlock.objects.filter(user=scores_user).select_related("task__event"):
		# this is `set` update, not queryset.update -- just a local variable.
		user_unlocks.update(v.id for v in UnlockTask.objects.filter(event=u.task.event, ordering__lte=u.task.ordering))
	
	#### DATATABLE ENTRY GENERATION ####

	scores_data = []

	# {song_id: [ratings]}
	all_charts = {}
	any_hidden = False

	chart_query = Chart.objects.all().select_related("song", "song__version", "difficulty")
	same_user = (logged_in_user.id == user_id)

	for chart in chart_query:
		entry = {}
		default_chart = True
		amethyst_required = True
		if chart.song.removed:
			default_chart = False
			amethyst_required = False
			entry["0"] = UNAVAILABLE
			entry["1"] = UNAVAILABLE
		elif chart.hidden:
			any_hidden = True
			default_chart = False
			amethyst_required = False
			entry["0"] = VISIBLE
			entry["1"] = VISIBLE
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
			flare_gauge = db_score.flare_gauge
		else:
			score = 0
			timestamp = 0
			clearType = 0
			quality = None
			flare_gauge = None

		if (clearType == 1) and (chart.id in aux) and (aux[chart.id].life4_clear):
			clearType = 2

		goal = None
		if (target_quality is not None) and (chart.quality_breakpoints):
			goal = compute_goal(target_quality, chart)

		notes = ''
		bookmarked = False
		if same_user and (chart.id in aux):
			notes = aux[chart.id].notes
			bookmarked = aux[chart.id].bookmark

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
		entry['flare_gauge'] = flare_gauge
		entry['goal'] = goal
		entry['spiced'] = spice is not None
		entry['chart_id'] = chart.id
		entry['distance'] = (goal - score) if goal else 0
		entry['timestamp'] = timestamp
		entry['notes'] = notes
		entry['bookmarked'] = bookmarked
		entry['default_chart'] = default_chart
		entry['amethyst_required'] = amethyst_required
		entry['hidden'] = chart.hidden
		entry['removed'] = chart.song.removed
		entry['tracked'] = chart.tracked
		entry['active_requirement'] = False  # i hate doing this but i don't see another way to get datatables.js to actually let me set this column.
		scores_data.append(entry)

	scores_data.sort(key=lambda x: x['quality'] or 0, reverse=True)
	for i, entry in enumerate(scores_data):
		entry['rank'] = i + 1

	life4_reqs = {
		'trials': {'best': scores_user.best_trial, 'second': scores_user.second_best_trial},
		'calories': scores_user.best_calorie_burn,
		'consecutives': {2: scores_user.best_two_consecutive, 3: scores_user.best_three_consecutive},
	}

	requirement_targets = user_targets(scores_user, white_cab.version_id)
	return render(request, 'scorebrowser/scores.html', {
		'scores': json.dumps(scores_data),
		'cabinets': cab_names,
		'versions': version_names,
		'white_version': white_cab.version_id,
		'all_charts': json.dumps(all_charts),
		'romanized_titles': logged_in_user.romanized_titles,
		'life4_reqs': json.dumps(life4_reqs),
		'requirement_targets': json.dumps(requirement_targets),
		'selected_rank': scores_user.selected_rank,
		'selected_flare': scores_user.selected_flare,
		'selected_visibility_id': logged_in_user.visibility_id,
		'visibilities': ProfileVisibility.objects.all().order_by('id'),
		'ask_for_vis': (same_user and not logged_in_user.vis_asked),
		'any_hidden': any_hidden,
		'same_user': same_user,
		'username': scores_user.django_user.username,
	})