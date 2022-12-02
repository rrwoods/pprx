from django.http import HttpResponse

def index(request):
	return HttpResponse("Hi!  This is the score browser index.")