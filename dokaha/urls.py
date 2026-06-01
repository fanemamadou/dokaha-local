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
    path('credits/', views.credits_list, name='credits_list'),
    path('credits/<int:vente_id>/relance/', views.credits_relance, name='credits_relance'),
    path('credits/<int:vente_id>/payer/', views.credits_payer, name='credits_payer'),
    path('credits/<int:vente_id>/paiement/', views.credits_paiement_partiel, name='credits_paiement'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/export-excel/', views.finance_export_excel, name='finance_export_excel'),
    path('cheptel/', views.cheptel, name='cheptel'),
    path('depense/add/', views.depense_add, name='depense_add'),
    path('sante/', views.sante_form, name='sante'),
    path('rapport-jour/', views.rapport_jour, name='rapport_jour'),
    path('terrain/', views.terrain, name='terrain'),
]
