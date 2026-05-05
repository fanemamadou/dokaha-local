from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from .models import CategorieStock, MouvementStock, AlertesStock
from .forms import MouvementStockForm, StockEntreeForm, StockSortieForm
# Helper pour vérifier si un utilisateur est dans le groupe DG
def is_user_dg(user):
    return user.groups.filter(name='DG').exists() or user.is_superuser


# 📦 Dashboard Stock (liste des catégories + stocks)
@login_required
def stock_dashboard(request):
    categories = CategorieStock.objects.all()
    alertes = AlertesStock.objects.filter(acquittee=False)[:5]
    
    context = {
        'categories': categories,
        'alertes': alertes,
        'title': '📦 Gestion du Stock', 'is_dg': is_user_dg(request.user)
    }
    return render(request, 'gestion/stock_dashboard.html', context)

# 📥 Formulaire Entrée (exclut les œufs)
@login_required
def stock_entree_add(request):
    if request.method == 'POST':
        form = StockEntreeForm(request.POST)
        if form.is_valid():
            mvt = form.save(commit=False)
            mvt.type_mouvement = 'entree'
            mvt.cree_par = request.user
            mvt.save()
            messages.success(request, f"✅ Entrée enregistrée : +{mvt.quantite} {mvt.categorie.unite_mesure}")
            return redirect('stock_dashboard')
    else:
        form = StockEntreeForm()
    return render(request, 'gestion/stock_form.html', {'form': form, 'title': '📥 Entrée de Stock', 'type': 'entree'})

# 📤 Formulaire Sortie (exclut les œufs)
@login_required
def stock_sortie_add(request):
    if request.method == 'POST':
        form = StockSortieForm(request.POST)
        if form.is_valid():
            mvt = form.save(commit=False)
            mvt.type_mouvement = 'sortie'
            mvt.cree_par = request.user
            mvt.save()
            messages.success(request, f"✅ Sortie enregistrée : -{mvt.quantite} {mvt.categorie.unite_mesure}")
            return redirect('stock_dashboard')
    else:
        form = StockSortieForm()
    return render(request, 'gestion/stock_form.html', {'form': form, 'title': '📤 Sortie de Stock', 'type': 'sortie'})

# 🗂️ Gestion des catégories (CRUD simple)
@login_required
def stock_categories(request):
    if request.method == 'POST' and 'add_category' in request.POST:
        nom = request.POST.get('nom')
        unite = request.POST.get('unite_mesure', 'unités')
        seuil = request.POST.get('seuil_alerte', 10)
        if nom:
            CategorieStock.objects.get_or_create(nom=nom, defaults={'unite_mesure': unite, 'seuil_alerte': seuil})
            messages.success(request, f"✅ Catégorie '{nom}' créée")
            return redirect('stock_categories')
    
    categories = CategorieStock.objects.all()
    return render(request, 'gestion/stock_categories.html', {'categories': categories, 'title': '🗂️ Catégories'})

# 📈 Historique Graphique (Vue restaurée)
@login_required
def historique_graphique(request):
    """Affiche la page d'historique (placeholder pour Chart.js plus tard)."""
    return render(request, 'gestion/historique_graphique.html', {
        'title': '📈 Historique Graphique'
    })


@login_required
def dg_dashboard(r):
    if not (r.user.groups.filter(name="DG").exists() or r.user.is_superuser):
        return redirect("dg_refuse")
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Avg
    from gestion.models import ProductionOeufs, Vente, Poulailler, CategorieStock, MouvementStock
    
    today = timezone.now().date()
    premier = today.replace(day=1)
    trente_j = today - timedelta(days=30)
    
    # 💰 Financier
    ca_mois = Vente.objects.filter(date__gte=premier).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    depenses_mois = 0  # À activer si modèle Depense existe
    marge_brute = ca_mois - depenses_mois
    taux_marge = round((marge_brute / ca_mois * 100), 1) if ca_mois > 0 else 0
    
    # 📈 Production 30j
    oeufs_30j = ProductionOeufs.objects.filter(date__gte=trente_j).aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 0
    poules_actives = Poulailler.objects.aggregate(Sum('effectif_initial'))['effectif_initial__sum'] or 1
    taux_ponte = round((oeufs_30j / (poules_actives * 30)) * 100, 1) if poules_actives > 0 else 0
    
    # 📦 Stock
    cat = CategorieStock.objects.filter(nom__in=['Œufs', 'Oeufs']).first()
    stock_oeufs = 0
    if cat:
        e = MouvementStock.objects.filter(categorie=cat, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
        s = MouvementStock.objects.filter(categorie=cat, type_mouvement='sortie').aggregate(Sum('quantite'))['quantite__sum'] or 0
        stock_oeufs = int(e - s)
    valeur_stock = stock_oeufs // 30 * 15000  # estimation
    
    # Formatage nombres
    def fmt(n): return f"{int(n):,}".replace(",", " ") if n else "0"
    
    ctx = {
        'title': '🎯 Bilan DG',
        'ca_mois': fmt(ca_mois), 'depenses_mois': fmt(depenses_mois), 'marge_brute': fmt(marge_brute),
        'taux_marge': taux_marge, 'cout_par_oeuf': 0,
        'oeufs_30j': fmt(oeufs_30j), 'taux_ponte_moyen': taux_ponte, 'mortalite': 0,
        'poules_actives': fmt(poules_actives), 'stock_oeufs': fmt(stock_oeufs), 'valeur_stock': fmt(valeur_stock),
        'batiments_actifs': Poulailler.objects.filter(effectif_initial__gt=0).count(),
        'effectif_total': fmt(poules_actives),
        'score_rentabilite': min(100, max(0, taux_marge + 20)),
        'score_effica': min(100, max(0, taux_ponte * 2)),
        'score_sanitaire': 100,
        'alertes': []
    }
    return render(r, 'gestion/dg_dashboard.html', ctx)


@login_required
def dg_refuse(r):
    return render(r, "gestion/dg_refuse.html", {"title": "⛔ Accès refusé"})
