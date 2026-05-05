from django.contrib import admin
from django.urls import path
from gestion import views
from gestion import public_views

urlpatterns = [
    path('', public_views.landing, name='landing'),
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dg/', views.dg_dashboard, name='dg_dashboard'),
    path('vente/', views.vente_list, name='vente_list'),
    path('vente/add/', views.vente_choice, name='vente_choice'),
    path('vente/oeufs/', views.vente_form, name='vente_oeufs'),
    path('vente/poulets/', views.vente_form, name='vente_poulets'),
    path('vente/autres/', views.vente_form, name='vente_autres'),
    path('acces-refuse/', views.acces_refuse, name='acces_refuse'),
    # 📦 Routes Stock - activées (vues présentes dans views.py)
# #     # TEMP: path('stock/', views.stock_dashboard, name='stock_dashboard'),
# #     # TEMP: path('stock/ajouter/', views.stock_ajouter, name='stock_ajouter'),
# #     # TEMP: path('stock/historique/', views.stock_historique, name='stock_historique'),
]
