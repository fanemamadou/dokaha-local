from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from gestion.models import ProductionOeufs, Vente, Poulailler, CategorieStock, MouvementStock

def fmt(n): return f"{int(n):,}".replace(",", " ") if n else "0"

def landing(request):
    today = timezone.now().date()
    trente_j = today - timedelta(days=30)
    
    total_oeufs = ProductionOeufs.objects.aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 0
    poules = Poulailler.objects.aggregate(Sum('effectif_initial'))['effectif_initial__sum'] or 0
    ca_30j = Vente.objects.filter(date__gte=trente_j).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    
    cat = CategorieStock.objects.filter(nom__in=['Œufs', 'Oeufs']).first()
    stock = 0
    if cat:
        e = MouvementStock.objects.filter(categorie=cat, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
        s = MouvementStock.objects.filter(categorie=cat, type_mouvement='sortie').aggregate(Sum('quantite'))['quantite__sum'] or 0
        stock = int(e - s)
        
    return render(request, 'public/landing.html', {
        'total_oeufs': fmt(total_oeufs), 'poules': fmt(poules), 'ca_30j': fmt(ca_30j), 'stock': fmt(stock),
        'title': 'Tropic Volaille - Excellence Avicole'
    })
