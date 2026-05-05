from django.contrib import admin
from .models import (
    ProductionOeufs, Vente, Depense, Poulailler, 
    CategorieStock, MouvementStock, Produit,
    Client, LotPoules, MouvementCheptel, SortiePoules,
    Sante, AlertesStock
)

# 🥚 Production Œufs
@admin.register(ProductionOeufs)
class ProductionOeufsAdmin(admin.ModelAdmin):
    list_display = ('date', 'poulailler', 'nombre_oeufs', 'oeufs_casses', 'commentaire')
    list_filter = ('poulailler', 'date')
    date_hierarchy = 'date'

# 💰 Ventes
@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'type_vente', 'montant_total', 'montant_paye', 'montant_restant')
    list_filter = ('type_vente', 'date', 'client')
    search_fields = ('client__nom', 'client__telephone')
    date_hierarchy = 'date'

# 💸 Dépenses
@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'categorie', 'montant', 'description')
    list_filter = ('categorie', 'date')
    date_hierarchy = 'date'

# 🏠 Poulaillers
@admin.register(Poulailler)
class PoulaillerAdmin(admin.ModelAdmin):
    list_display = ('nom', 'capacite', 'occupation_actuelle', 'actif')
    list_filter = ('actif',)

# 👥 Clients
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'email', 'ville')
    search_fields = ('nom', 'telephone', 'email')

# 📦 Catégories Stock
@admin.register(CategorieStock)
class CategorieStockAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)

# 📦 Produits (LE MODÈLE QUI BLOQUAIT)
@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'unite', 'stock_actuel', 'seuil_alerte', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('nom', 'description')
    list_editable = ('stock_actuel', 'seuil_alerte', 'actif')
    fieldsets = (
        ('Informations', {'fields': ('nom', 'categorie', 'description', 'unite')}),
        ('Gestion Stock', {'fields': ('stock_actuel', 'seuil_alerte', 'actif')}),
    )

# 📦 Mouvements Stock
@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date', 'produit', 'type_mouvement', 'quantite', 'commentaire')
    list_filter = ('type_mouvement', 'produit__categorie', 'date')
    date_hierarchy = 'date'

# 🐔 Lots de poules
@admin.register(LotPoules)
class LotPoulesAdmin(admin.ModelAdmin):
    list_display = ('date_arrivee', 'race', 'nombre_initial', 'poulailler', 'actif')
    list_filter = ('race', 'poulailler', 'actif')

# 📊 Mouvements cheptel
@admin.register(MouvementCheptel)
class MouvementCheptelAdmin(admin.ModelAdmin):
    list_display = ('date', 'lot', 'type_mouvement', 'nombre', 'raison')
    list_filter = ('type_mouvement', 'lot__race', 'date')

# 🚪 Sorties poules
@admin.register(SortiePoules)
class SortiePoulesAdmin(admin.ModelAdmin):
    list_display = ('date', 'lot', 'nombre', 'motif', 'destination')
    list_filter = ('motif', 'date')

# 🏥 Santé
@admin.register(Sante)
class SanteAdmin(admin.ModelAdmin):
    list_display = ('date', 'lot', 'type_soins', 'cout', 'description')
    list_filter = ('type_soins', 'date')

# ⚠️ Alertes Stock
@admin.register(AlertesStock)
class AlertesStockAdmin(admin.ModelAdmin):
    list_display = ('date', 'produit', 'niveau_alerte', 'message')
    list_filter = ('niveau_alerte', 'date')
