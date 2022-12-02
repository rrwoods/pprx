from django.urls import path
from . import views

urlpatterns = [
	path('', views.landing, name='landing'),
	path('charts', views.charts, name='charts'),
]