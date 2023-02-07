from django.urls import path
from . import views

urlpatterns = [
	path('', views.landing, name='landing'),
	path('charts', views.charts, name='charts'),
	path('scores', views.scores, name='scores'),
	path('unlocks', views.unlocks, name='unlocks'),
	path('update_unlock', views.update_unlock, name='update_unlock'),
	path('goals', views.goals, name='goals'),
	path('set_goal', views.set_goal, name='set_goal'),
]