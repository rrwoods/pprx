from django import template

DIFFICULTY_NAMES = ['Beginner', 'Basic', 'Difficult', 'Expert', 'Challenge']
register = template.Library()

@register.filter
def difficulty(n):
	return DIFFICULTY_NAMES[n]
