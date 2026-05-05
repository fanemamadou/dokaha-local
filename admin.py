from django.contrib import admin
from .models import Poulailler

@admin.register(Poulailler)
class PoulaillerAdmin(admin.ModelAdmin):
    list_display = ('nom', 'capacite', 'race', 'actif', 'date_creation')
    list_filter = ('actif', 'race')
    search_fields = ('nom', 'race')