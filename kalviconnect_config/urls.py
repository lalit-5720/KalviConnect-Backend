from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/teacher/', include('academy.urls')),
    path('api/parent/', include('academy.parent_urls')),
]
