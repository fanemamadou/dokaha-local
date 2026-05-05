from django.contrib import admin
from .models import (
    ProductionOeufs, Vente, Depense, Poulailler, 
    CategorieStock, MouvementStock, Produit,
    Client, LotPoules, MouvementCheptel, SortiePoules,
    Sante, AlertesStock
)
# Enregistrement générique : évite toute erreur list_display/list_filter
admin.site.register(ProductionOeufs)
admin.site.register(Vente)
admin.site.register(Depense)
admin.site.register(Poulailler)
admin.site.register(CategorieStock)
admin.site.register(MouvementStock)
admin.site.register(Produit)
admin.site.register(Client)
admin.site.register(LotPoules)
admin.site.register(MouvementCheptel)
admin.site.register(SortiePoules)
admin.site.register(Sante)
admin.site.register(AlertesStock)
