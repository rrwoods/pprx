from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda req: redirect('/scorebrowser/')),
    path('admin/', admin.site.urls),
    path('scorebrowser/', include('scorebrowser.urls')),
]
