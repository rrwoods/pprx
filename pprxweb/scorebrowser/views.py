from django.shortcuts import render
from .models import *

def landing(request):
	login_url_template = 'https://3icecream.com/oauth/authorize?client_id={}&response_type=code&scope=read_scores&redirect_uri={}'
	login_url = login_url_template.format('3d7da688edfc426b9e63615af6210870', 'http://localhost:8000/scorebrowser/charts')
	return render(request, 'scorebrowser/landing.html', {'login_url': login_url})

def charts(request):
	charts = Chart.objects.exclude(spice=None).order_by('-spice')
	return render(request, 'scorebrowser/charts.html', {
		'charts': charts,
	})