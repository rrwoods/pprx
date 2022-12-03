from django.urls import path
from . import views

urlpatterns = [
	path('', views.landing, name='landing'),
	path('charts', views.charts, name='charts'),
	path('scores', views.scores, name='scores'),
	path('visibility', views.visibility, name='visibility'),
	path('update_visibility', views.update_visibility, name='update_visibility'),
	path('goals', views.goals, name='goals'),
	path('set_goal', views.set_goal, name='set_goal'),
]