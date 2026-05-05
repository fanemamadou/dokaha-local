from decimal import Decimal
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import ProductionOeufs, CategorieStock, MouvementStock
from .forms import StockEntreeForm, StockSortieForm



@login_required
def stock_dashboard(r):
    return render(r, "gestion/stock_dashboard.html", {"categories": CategorieStock.objects.all(), "title": "📦 Stock"})

@login_required
def stock_entree_add(r):
    if r.method == "POST":
        f = StockEntreeForm(r.POST)
        if f.is_valid():
            m = f.save(commit=False)
            m.type_mouvement = "entree"
            m.cree_par = r.user
            m.save()
            messages.success(r, "✄ Entrée enregistrée")
            return redirect("stock_dashboard")
    else:
        f = StockEntreeForm()
    return render(r, "gestion/stock_form.html", {"form": f, "title": "📥 Entrée", "type": "entree"})

@login_required
def stock_sortie_add(r):
    if r.method == "POST":
        f = StockSortieForm(r.POST)
        if f.is_valid():
            m = f.save(commit=False)
            m.type_mouvement = "sortie"
            m.cree_par = r.user
            m.save()
            messages.success(r, "┄ Sortie enregistrée")
            return redirect("stock_dashboard")
    else:
        f = StockSortieForm()
    return render(r, "gestion/stock_form.html", {"form": f, "title": "📤 Sortie", "type": "sortie"})

@login_required
def stock_categories(r):
    if r.method == "POST" and "add_category" in r.POST:
        n = r.POST.get("nom")
        if n:
            CategorieStock.objects.get_or_create(nom=n, defaults={"unite_mesure": r.POST.get("unite_mesure", "unités"), "seuil_alerte": r.POST.get("seuil_alerte", 10)})
            messages.success(r, f"✅ '{n}' créée")
            return redirect("stock_categories")
    return render(r, "gestion/stock_categories.html", {"categories": CategorieStock.objects.all(), "title": "🗂 Catégories"})

@login_required
def historique_graphique(r):
    return render(r, "gestion/historique_graphique.html", {"title": "📶 Historique"})


def fmt(n):
    return f"{int(n):,}".replace(",", " ") if n else "0"


@login_required
def dg_dashboard(r):
    if not (r.user.groups.filter(name="DG").exists() or r.user.is_superuser):
        return redirect("dg_refuse")
    
    from django.utils import timezone
    from datetime import timedelta, date
    from django.db.models import Sum, Count, Avg, F
    from gestion.models import ProductionOeufs, Vente, Depense, Poulailler, CategorieStock, MouvementStock
    
    today = timezone.now().date()
    premier_mois = today.replace(day=1)
    trente_j = today - timedelta(days=30)
    six_mois = today - timedelta(days=180)
    
    # 💰 Indicateurs Financiers
    ca_mois = Vente.objects.filter(date__gte=premier_mois).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    depenses_mois = None  # Si le modèle Depense existe
    try:
        from gestion.models import Depense
        depenses_mois = Depense.objects.filter(date__gte=premier_mois).aggregate(Sum('montant'))['montant__sum'] or 0
    except:
        depenses_mois = 0
    marge_brute = ca_mois - depenses_mois
    taux_marge = round((marge_brute / ca_mois * 100), 1) if ca_mois > 0 else 0
    cout_par_oeuf = round(depenses_mois / (ProductionOeufs.objects.filter(date__gte=premier_mois).aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 1), 0) if depenses_mois > 0 else 0
    
    # 📈 Performance Production (30j)
    oeufs_30j = ProductionOeufs.objects.filter(date__gte=trente_j).aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 0
    poules_actives = Poulailler.objects.aggregate(Sum('effectif_initial'))['effectif_initial__sum'] or 1
    taux_ponte_moyen = round((oeufs_30j / (poules_actives * 30)) * 100, 1) if poules_actives > 0 else 0
    # Mortalité (si modèle Sante existe)
    mortalite = 0
    try:
        from gestion.models import Sante
        mortalite = Sante.objects.filter(date__gte=trente_j, traitement__icontains='mortal').count()
    except:
        pass
    
    # 📦 Stock & Ressources
    cat_oeufs = CategorieStock.objects.filter(nom__in=['Œufs', 'Oeufs']).first()
    stock_oeufs = 0
    valeur_stock = 0
    if cat_oeufs:
        entrees = MouvementStock.objects.filter(categorie=cat_oeufs, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
        sorties = MouvementStock.objects.filter(categorie=cat_oeufs, type_mouvement='sortie').aggregate(Sum('quantite'))['quantite__sum'] or 0
        stock_oeufs = int(entrees - sorties)
        # Valeur estimée : stock × prix moyen des ventes récentes
        prix_moyen = Vente.objects.filter(type_vente='oeufs', date__gte=trente_j).aggregate(Avg('prix_plateau'))['prix_plateau__avg'] or 15000
        valeur_stock = stock_oeufs // 30 * prix_moyen  # conversion œufs → plateaux × prix
    
    batiments_actifs = Poulailler.objects.filter(effectif_initial__gt=0).count()
    effectif_total = poules_actives
    
    # 📊 CA 6 derniers mois (pour graphique)
    from collections import OrderedDict
    ca_6mois = OrderedDict()
    for i in range(5, -1, -1):
        mois = today.replace(day=1) - timedelta(days=30*i)
        k = mois.strftime('%m/%Y')
        ca_6mois[k] = Vente.objects.filter(date__year=mois.year, date__month=mois.month).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    
    # 📋 Synthèse Direction (scores simplifiés)
    score_rentabilite = min(100, max(0, taux_marge + 20)) if ca_mois > 0 else 0
    score_effica = min(100, max(0, taux_ponte_moyen * 2))  # objectif 50% = 100pts
    score_sanitaire = 100 - min(100, mortalite * 10)
    
    ctx = {
        'title': '🎯 Tableau de Bord Direction',
        'ca_mois': fmt(ca_mois), 'depenses_mois': fmt(depenses_mois), 'marge_brute': fmt(marge_brute),
        'taux_marge': taux_marge, 'cout_par_oeuf': fmt(cout_par_oeuf),
        'oeufs_30j': fmt(oeufs_30j), 'taux_ponte_moyen': taux_ponte_moyen, 'mortalite': mortalite,
        'poules_actives': fmt(poules_actives), 'stock_oeufs': fmt(stock_oeufs), 'valeur_stock': fmt(valeur_stock),
        'batiments_actifs': batiments_actifs, 'effectif_total': fmt(effectif_total),
        'ca_6mois_labels': list(ca_6mois.keys()), 'ca_6mois_data': list(ca_6mois.values()),
        'score_rentabilite': score_rentabilite, 'score_effica': score_effica, 'score_sanitaire': score_sanitaire,
        'alertes': [] if (taux_ponte_moyen >= 30 and mortalite <= 2) else ['⚠️ Surveiller les indicateurs']
    }
    return render(r, 'gestion/dg_dashboard.html', ctx)

@login_required
def dg_refuse(r):
    return render(r, "gestion/dg_refuse.html", {"title": "♅ Accès refusé"})
@login_required





@login_required
def vente_list(request):
    from gestion.models import Vente
    from django.db.models import Sum
    ventes = Vente.objects.all().order_by('-date')[:100]
    t_ca = Vente.objects.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    t_plt = Vente.objects.aggregate(Sum('plateaux'))['plateaux__sum'] or 0
    def fmt(n): return f"{int(n):,}".replace(",", " ") if n else "0"
    return render(request, 'gestion/vente_list.html', {
        'ventes': ventes, 'total_ca': fmt(t_ca), 'total_plt': fmt(t_plt),
        'title': '💰 Historique des Ventes'
    })

@login_required
def vente_choice(request):
    return render(request, 'gestion/vente_choice.html', {'title': '💰 Type de vente'})

@login_required
@login_required
def dashboard(request):
    """Dashboard principal - redirection intelligente"""
    if request.user.is_superuser or "DG" in [g.name for g in request.user.groups.all()]:
        from django.shortcuts import redirect
        return redirect('/dg/')
    # Pour les autres rôles : stats de base
    from gestion.models import Vente, Stock
    from django.db.models import Sum
    from django.utils import timezone
    
    ca_mois = Vente.objects.filter(date__month=timezone.now().month).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    stock = Stock.objects.last()
    
    return render(request, 'gestion/dashboard.html', {
        'ca_mois': f"{int(ca_mois):,}".replace(",", " ") if ca_mois else "0",
        'stock_actuel': stock.quantite if stock else 0,
        'title': '📊 Dashboard'
    })


@login_required

@login_required
def vente_form(request):
    from django.utils import timezone
    from gestion.models import Vente

    path = request.path
    if 'poulets' in path: type_v = 'poulets'
    elif 'autres' in path: type_v = 'autres'
    else: type_v = 'oeufs'

    if request.method == 'POST':
        client = request.POST.get('client', 'Client comptoir').strip()
        plateaux = int(request.POST.get('plateaux', 0) or 0)
        prix = Decimal(request.POST.get('prix_plateau', 0) or 0)
        paye = Decimal(request.POST.get('montant_paye', 0) or 0)

        # 🔒 Calcul backend sécurisé (ignore le JS du navigateur)
        montant_total = plateaux * prix
        montant_restant = max(Decimal(0), montant_total - paye)

        Vente.objects.create(
            date=timezone.now().date(),
            client=client,
            type_vente=type_v,
            plateaux=plateaux,
            prix_plateau=prix,
            montant_total=montant_total,
            montant_paye=paye,
            montant_restant=montant_restant
        )
        return redirect('/vente/')

    return render(request, 'gestion/vente_form.html', {'type_vente': type_v, 'title': f'📝 Vente de {type_v}'})

