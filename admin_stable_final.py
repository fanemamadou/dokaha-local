from django.contrib import admin
from gestion.models import AlertesStock, CategorieStock, Client, Depense, LotPoules, MouvementCheptel, MouvementStock, Poulailler, ProductionOeufs, Sante, SortiePoules, Vente

@admin.register(AlertesStock)
class AlertesStockAdmin(admin.ModelAdmin):
    pass

@admin.register(CategorieStock)
class CategorieStockAdmin(admin.ModelAdmin):
    pass

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    pass

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    pass

@admin.register(LotPoules)
class LotPoulesAdmin(admin.ModelAdmin):
    pass

@admin.register(MouvementCheptel)
class MouvementCheptelAdmin(admin.ModelAdmin):
    pass

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    pass

@admin.register(Poulailler)
class PoulaillerAdmin(admin.ModelAdmin):
    pass

@admin.register(ProductionOeufs)
class ProductionOeufsAdmin(admin.ModelAdmin):
    pass

@admin.register(Sante)
class SanteAdmin(admin.ModelAdmin):
    pass

@admin.register(SortiePoules)
class SortiePoulesAdmin(admin.ModelAdmin):
    pass

@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    pass

