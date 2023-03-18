from django.urls import path
from . import views

urlpatterns = [
	path('', views.landing, name='landing'),
	path('logged_in', views.logged_in, name='logged_in'),
	path('charts', views.charts, name='charts'),
	path('scores', views.scores, name='scores'),
	path('unlocks', views.unlocks, name='unlocks'),
	path('update_unlock', views.update_unlock, name='update_unlock'),
	path('update_unlock_event', views.update_unlock_event, name='update_unlock_event'),
	path('set_goal', views.set_goal, name='set_goal'),

	path('hello', views.hello, name='hello'),
]