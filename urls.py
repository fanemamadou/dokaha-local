# dokaha/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),  # ← INDISPENSABLE : délègue tout le reste à gestion/urls.py
]