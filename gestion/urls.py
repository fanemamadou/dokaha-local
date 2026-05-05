from django.urls import path
from . import views
app_name = 'gestion'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('production/add/', views.production_add, name='production_add'),
    path('vente/add/', views.vente_add, name='vente_add'),
    path('depense/add/', views.depense_add, name='depense_add'),
]
