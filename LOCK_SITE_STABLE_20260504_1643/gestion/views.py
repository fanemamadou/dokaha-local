from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.contrib.auth.models import User
from django.contrib import messages
from decimal import Decimal
from gestion.models import ProductionOeufs, Vente, Depense, Poulailler, CategorieStock, MouvementStock, Produit
from .forms import StockEntreeForm, StockSortieForm

# =============================================================================
# 📦 VUES STOCK (placeholders garantis fonctionnels)
# =============================================================================
@login_required
def stock_historique(request):
    """Historique des mouvements Stock"""
    return render(request, 'gestion/base.html', {'title': '📜 Historique Stock', 'user': request.user})

# =============================================================================
# 🎯 AUTRES VUES (placeholders si absentes)
# =============================================================================
@login_required
def dashboard(request):
    return render(request, 'gestion/base.html', {'title': 'Dashboard', 'user': request.user})

@login_required
def dg_dashboard(request):
    return render(request, 'gestion/base.html', {'title': 'Dashboard DG', 'user': request.user})

@login_required
def vente_list(request):
    ventes = Vente.objects.all().order_by('-date')[:100]
    return render(request, 'gestion/vente_list.html', {'ventes': ventes, 'title': 'Ventes', 'user': request.user})

@login_required
def vente_choice(request):
    return render(request, 'gestion/vente_choice.html', {'title': 'Type de vente', 'user': request.user})

@login_required
def vente_form(request, type_vente):
    return render(request, 'gestion/vente_form.html', {'type_vente': type_vente, 'title': f'Vente {type_vente}', 'user': request.user})

@login_required
def acces_refuse(request):
    return render(request, 'gestion/acces_refuse.html', {'title': '🚫 Accès Refusé', 'user': request.user})

# 📦 VUES STOCK - Ajoutées proprement (ne pas toucher)
@login_required
def stock_historique(request):
    return render(request, 'gestion/base.html', {'title': '📜 Historique Stock', 'user': request.user})
@login_required
def stock_dashboard(request):
    """Dashboard Stock : calcule le stock par catégorie (structure réelle de la BDD)"""
    from django.db.models import Sum
    from gestion.models import Produit, MouvementStock
    
    produits = Produit.objects.filter(actif=True).select_related('categorie').order_by('categorie', 'nom')
    produits_data = []
    total_alertes = 0
    
    # Cache des stocks par catégorie pour éviter les requêtes répétées
    cat_stocks = {}
    
    for p in produits:
        cat_id = p.categorie_id
        if cat_id not in cat_stocks:
            entrees = MouvementStock.objects.filter(categorie_id=cat_id, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
            sorties = MouvementStock.objects.filter(categorie_id=cat_id, type_mouvement='sortie').aggregate(Sum('quantite'))['quantite__sum'] or 0
            ajust   = MouvementStock.objects.filter(categorie_id=cat_id, type_mouvement='ajustement').aggregate(Sum('quantite'))['quantite__sum'] or 0
            pertes  = MouvementStock.objects.filter(categorie_id=cat_id, type_mouvement='perte').aggregate(Sum('quantite'))['quantite__sum'] or 0
            cat_stocks[cat_id] = float(entrees - sorties + ajust - pertes)
            
        stock = cat_stocks[cat_id]
        seuil = p.seuil_alerte or 0
        
        p_data = {'produit': p, 'stock': stock, 'seuil': seuil, 'categorie': p.categorie}
        produits_data.append(p_data)
        
        if stock <= seuil and seuil > 0:
            total_alertes += 1
            
    return render(request, 'gestion/stock_dashboard.html', {
        'title': '📦 Gestion des Stocks',
        'produits': produits_data,
        'alertes': [p for p in produits_data if p['stock'] <= p['seuil'] and p['seuil'] > 0],
        'total_produits': len(produits_data),
        'total_alertes': total_alertes,
        'user': request.user
    })
@login_required
def stock_ajouter(request):
    """Formulaire mouvement stock (compatible catégorie + choices réels)"""
    from .forms import StockMouvementForm
    from .models import MouvementStock, CategorieStock
    from django.utils import timezone
    from django.contrib import messages
    from decimal import Decimal
    
    if request.method == 'POST':
        form = StockMouvementForm(request.POST)
        if form.is_valid():
            cat = form.cleaned_data['categorie']  # Le form renvoie maintenant une CategorieStock
            type_mvt = form.cleaned_data['type_mouvement']  # 'entree', 'sortie', etc.
            quantite = Decimal(str(form.cleaned_data['quantite']))
            commentaire = form.cleaned_data.get('commentaire', '')
            
            MouvementStock.objects.create(
                categorie=cat,
                date=timezone.now(),
                type_mouvement=type_mvt,
                quantite=quantite,
                prix_unitaire=Decimal('0'),
                montant_total=Decimal('0'),
                commentaire=commentaire,
                cree_par=request.user
            )
            messages.success(request, f"✅ {quantite} {cat.unite_mesure if cat.unite_mesure else 'unité(s)'} {type_mvt} enregistrée(s)")
            return redirect('/stock/')
    else:
        form = StockMouvementForm()
        
    return render(request, 'gestion/stock_ajouter.html', {
        'title': '📝 Ajouter un Mouvement Stock',
        'form': form,
        'user': request.user
    })
