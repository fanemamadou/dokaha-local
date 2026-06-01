from django.contrib import admin
from django.urls import path
from gestion import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mortalite/ajouter/', views.mortalite_form, name='mortalite_form'),
    path('vente/', views.vente_list, name='vente_list'),
    path('vente/add/', views.vente_choice, name='vente_choice'),
    path('stock/', views.stock_dashboard, name='stock_dashboard'),
    path('collecte/', views.collecte_oeufs, name='collecte_oeufs'),
    path('vente/oeufs/', views.vente_form, {'type_vente': 'oeufs'}, name='vente_oeufs'),
    path('vente/poulets/', views.vente_form, {'type_vente': 'poulets'}, name='vente_poulets'),
    path('vente/autres/', views.vente_form, {'type_vente': 'autres'}, name='vente_autres'),
]
