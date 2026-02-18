from django import template
from django.urls import reverse

DIFFICULTY_NAMES = ['Beginner', 'Basic', 'Difficult', 'Expert', 'Challenge']
register = template.Library()

@register.filter(name='times')
def times(number):
	return range(number)

@register.filter
def difficulty(n):
	return DIFFICULTY_NAMES[n]

@register.simple_tag(takes_context=True)
def abs_url(context, view_name):
	return context['request'].build_absolute_uri(reverse(view_name))

@register.filter(name='index')
def index(indexable, index):
	return indexable[index]
