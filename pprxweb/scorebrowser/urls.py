from django.urls import path
from . import views

urlpatterns = [
	# account management
	path('', views.landing, name='landing'),
	path('register', views.register, name='register'),
	path('activate/<uidb64>/<token>', views.activate, name='activate'),
	path('update_email', views.update_email_form, name='update_email'),
	path('update_password', views.update_password, name='update_password'),
	path('reset_password', views.reset_password, name='reset_password'),
	path('finish_reset/<uidb64>/<token>', views.finish_reset, name='finish_reset'),
	path('login', views.login_user, name='login'),
	path('link_sanbai', views.link_sanbai, name='link_sanbai'),
	path('finish_link', views.finish_link, name='finish_link'),
	path('logout', views.logout_user, name='logout'),

	# score fetching
	path('force_fetch', views.force_fetch, name='force_fetch'),
	path('fetch_scores', views.fetch_scores, name='fetch_scores'),

	# main pages
	path('scores', views.scores, name='scores'),
	path('unlocks', views.unlocks, name='unlocks'),

	# ajax db requests
	path('set_region', views.set_region, name='set_region'),
	path('set_romanized_titles', views.set_romanized_titles, name='set_romanized_titles'),
	path('update_unlock', views.update_unlock, name='update_unlock'),
	path('update_progressive_unlock', views.update_progressive_unlock, name='update_progressive_unlock'),
	path('update_unlock_event', views.update_unlock_event, name='update_unlock_event'),
	path('set_goal', views.set_goal, name='set_goal'),
	path('set_chart_notes', views.set_chart_notes, name='set_chart_notes'),
	path('set_chart_bookmark', views.set_chart_bookmark, name='set_chart_bookmark'),
	path('set_chart_life4', views.set_chart_life4, name='set_chart_life4'),
	path('set_selected_rank', views.set_selected_rank, name='set_selected_rank'),
	path('set_trials', views.set_trials, name='set_trials'),
	path('set_calories', views.set_calories, name='set_calories'),
	path('set_consecutives', views.set_consecutives, name='set_consecutives'),
	path('target_requirement', views.target_requirement, name='target_requirement'),
	path('untarget_requirement', views.untarget_requirement, name='untarget_requirement'),

	path('hello', views.hello, name='hello'),
]