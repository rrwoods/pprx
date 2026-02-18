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

	# admin-related pages
	path('forbidden', views.forbidden, name='forbidden'),
	path('admin', views.admin, name='admin'),
	path('manage_unlocks', views.manage_unlocks, name='manage_unlocks'),
	path('delete_task/<task_id>', views.delete_task, name='delete_task'),
	path('add_gp_pack/<event_id>', views.add_gp_pack, name='add_gp_pack'),
	path('add_extra_savior/<group_id>', views.add_extra_savior, name='add_extra_savior'),
	path('add_galaxy_brave/<group_id>', views.add_galaxy_brave, name='add_galaxy_brave'),
	path('add_event/<group_id>', views.add_event, name='add_event'),
	path('add_task/<event_id>', views.add_task, name='add_task'),
	path('default_charts', views.default_charts, name='default_charts'),

	# main pages
	path('scores/<user_id>', views.scores, name='scores'),
	path('scores', views.my_scores, name='scores'),
	path('unlocks', views.unlocks, name='unlocks'),

	# ajax db requests
	path('set_profile_visibility', views.set_profile_visibility, name='set_profile_visibility'),
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
	path('set_selected_flare', views.set_selected_flare, name='set_selected_flare'),
	path('set_trials', views.set_trials, name='set_trials'),
	path('set_calories', views.set_calories, name='set_calories'),
	path('set_consecutives', views.set_consecutives, name='set_consecutives'),
	path('target_requirement', views.target_requirement, name='target_requirement'),
	path('untarget_requirement', views.untarget_requirement, name='untarget_requirement'),

	# welcome pages
	path('hello', views.hello, name='hello'),
	path('howto', views.howto, name='howto'),
]