from django.contrib import admin
from django.shortcuts import redirect
from .models import ProductionOeufs, MouvementStock, Vente, Depense, Poulailler, Client, Sante, SortiePoules

@admin.register(ProductionOeufs)
class ProductionOeufsAdmin(admin.ModelAdmin):
    list_display = ('date', 'poulailler', 'nombre_oeufs', 'oeufs_casses')
    list_filter = ('date', 'poulailler')

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date', 'categorie', 'type_mouvement', 'quantite', 'cree_par')
    list_filter = ('type_mouvement', 'categorie', 'date')


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'categorie', 'montant', 'date')
    list_filter = ('categorie', 'date')

@admin.register(Poulailler)
class PoulaillerAdmin(admin.ModelAdmin):
    list_display = ('nom', 'effectif_initial')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone')

@admin.register(Sante)
class SanteAdmin(admin.ModelAdmin):
    list_display = ('date', 'poulailler', 'traitement')
    list_filter = ('date', 'poulailler')

@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'type_vente', 'plateaux', 'montant_total')

    def changelist_view(self, request, extra_context=None):
        return redirect('/vente/')

    def add_view(self, request, form_url='', extra_context=None):
        return redirect('/vente/add/')

