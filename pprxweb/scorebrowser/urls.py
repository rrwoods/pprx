from django.urls import path
from . import views

urlpatterns = [
	path('', views.landing, name='landing'),
	path('logged_in', views.logged_in, name='logged_in'),
	path('charts', views.charts, name='charts'),
	path('scores', views.scores, name='scores'),
	path('unlocks', views.unlocks, name='unlocks'),
	path('set_region', views.set_region, name='set_region'),
	path('set_romanized_titles', views.set_romanized_titles, name='set_romanized_titles'),
	path('update_unlock', views.update_unlock, name='update_unlock'),
	path('update_unlock_event', views.update_unlock_event, name='update_unlock_event'),
	path('set_goal', views.set_goal, name='set_goal'),
	path('set_chart_notes', views.set_chart_notes, name='set_chart_notes'),
	path('set_chart_bookmark', views.set_chart_bookmark, name='set_chart_bookmark'),
	path('set_chart_life4', views.set_chart_life4, name='set_chart_life4'),

	path('hello', views.hello, name='hello'),
]