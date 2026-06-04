from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from gestion import views

# --- Déconnexion personnalisée (GET autorisé) ---
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

def logout_view(request):
    logout(request)
    # Redirige vers la page de connexion configurée dans settings.py
    return HttpResponseRedirect('/admin/login/')
# -----------------------------------------------

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('', views.home_view, name='home'),
    path('admin/', admin.site.urls),
    
    # Authentification
    path('logout/', logout_view, name='logout'),
    
    # Principal
    path('dashboard/', views.dashboard, name='dashboard'),
    path('terrain/', views.terrain, name='terrain'),
    path('rapport-jour/', views.rapport_jour, name='rapport_jour'),
    
    # Production & Cheptel
    path('collecte/', views.collecte_oeufs, name='collecte_oeufs'),
    path('mortalite/ajouter/', views.mortalite_form, name='mortalite_form'),
    path('cheptel/', views.cheptel, name='cheptel'),
    path('sante/', views.sante_form, name='sante'),
    
    # Ventes
    path('ventes/', views.historique_ventes, name='historique_ventes'),
    path('vente/', views.vente_list, name='vente_list'),
    path('vente/choix/', views.vente_choice, name='vente_choice'),
    path('vente/oeufs/', views.vente_form, {'type_vente': 'oeufs'}, name='vente_oeufs'),
    path('vente/poulets/', views.vente_form, {'type_vente': 'poulets'}, name='vente_poulets'),
    path('vente/autres/', views.vente_form, {'type_vente': 'autres'}, name='vente_autres'),
    
    # Crédits
    path('credits/', views.credits_list, name='credits_list'),
    path('credits/<int:vente_id>/relance/', views.credits_relance, name='credits_relance'),
    path('credits/<int:vente_id>/payer/', views.credits_payer, name='credits_payer'),
    path('credits/<int:vente_id>/paiement/', views.credits_paiement_partiel, name='credits_paiement'),
    
    # Finance & Dépenses
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/export-excel/', views.finance_export_excel, name='finance_export_excel'),
    path('depenses/', views.historique_depenses, name='historique_depenses'),
    path('depense/add/', views.depense_add, name='depense_add'),
    
    # Stock
    path('stock/', views.stock_dashboard, name='stock_dashboard'),
    path('stock/ajouter/', views.stock_ajouter, name='stock_ajouter'),
    path('stock/historique/', views.stock_historique, name='stock_historique'),
]
