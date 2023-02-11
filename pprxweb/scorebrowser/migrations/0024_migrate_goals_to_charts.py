from django.db import migrations, models

def forward(apps, schema_editor):
	User = apps.get_model("scorebrowser", "User")
	updated_users = []
	for user in User.objects.all():
		user.goal_chart = user.goal_benchmark.chart
		updated_users.append(user)
	User.objects.bulk_update(updated_users, ['goal_chart'])

def backward(apps, schema_editor):
	# The rollback removes all goal charts rather than reinstating the benchmark that was there before.
	# This is to avoid needing to determine which benchmark was there before (if it even still exists).
	User = apps.get_model("scorebrowser", "User")
	User.objects.all().update(goal_chart=None)

class Migration(migrations.Migration):
	dependencies = [('scorebrowser', '0023_user_goal_chart')]

	operations = [migrations.RunPython(forward, backward)]