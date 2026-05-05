from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include
from gestion import views, views_stock

from gestion import public_views

urlpatterns = [
    path('', public_views.landing, name='landing'),
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dg/', views.dg_dashboard, name='dg_dashboard'),
    # 🐔 Module VENTES
    path('vente/', views.vente_list, name='vente_list'),
    path('vente/add/', views.vente_choice, name='vente_choice'),
    path('vente/oeufs/', views.vente_form, name='vente_oeufs'),
    path('vente/poulets/', views.vente_form, name='vente_poulets'),
    path('vente/autres/', views.vente_form, name='vente_autres'),
    # Autres routes existantes (si any)
]
