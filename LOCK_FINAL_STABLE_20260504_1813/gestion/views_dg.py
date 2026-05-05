from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg
from .models import ProductionOeufs, Vente, Depense, Poulailler, MouvementCheptel, CategorieStock, MouvementStock

def is_dg(user):
    """Vérifie si l'utilisateur appartient au groupe DG"""
    return user.groups.filter(name='DG').exists() or user.is_superuser

def dg_access_denied(request):
    '''Page d'erreur d'accès pour non-DG'''
    messages.warning(request, "🔐 Accès réservé au groupe Direction (DG).")
    return redirect('dashboard')

@login_required
@user_passes_test(is_dg, login_url='/dashboard/', redirect_field_name=None)
def dg_dashboard(request):
    """Tableau de bord direction avec indicateurs stratégiques"""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # 💰 INDICATEURS FINANCIERS
    ca_mois = Vente.objects.filter(date__gte=month_start).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    depenses_mois = Depense.objects.filter(date__gte=month_start).aggregate(Sum('montant'))['montant__sum'] or 0
    marge_brute = ca_mois - depenses_mois
    taux_marge = round((marge_brute / ca_mois * 100), 1) if ca_mois > 0 else 0
    
    # 📈 PERFORMANCE PRODUCTION
    prod_30j = ProductionOeufs.objects.filter(date__gte=today-timedelta(days=30))
    total_oeufs = prod_30j.aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 0
    
    # Taux ponte estimé : (œufs / (poules × jours)) × 100
    effectif_moy = sum(p.effectif_initial or 0 for p in Poulailler.objects.all())
    jours_period = 30
    taux_ponte_moy = round((total_oeufs / (effectif_moy * jours_period) * 100), 1) if effectif_moy > 0 else 0
    
    # Mortalité (via MouvementCheptel)
    mortalites_30j = MouvementCheptel.objects.filter(
        date__gte=today-timedelta(days=30), 
        type_mouvement='mortalite'
    ).aggregate(Sum('nombre_poules'))['nombre_poules__sum'] or 0
    effectif_total = sum(p.effectif_initial or 0 for p in Poulailler.objects.all())
    taux_mortalite = round((mortalites_30j / effectif_total * 100), 2) if effectif_total > 0 else 0
    
    # Coût par œuf (simplifié)
    cout_oeuf = round(depenses_mois / total_oeufs, 2) if total_oeufs > 0 else 0

    # 📦 STOCK & LOGISTIQUE
    stock_valeur = 0
    alertes_stock = []
    for cat in CategorieStock.objects.all():
        actuel = cat.stock_actuel()
        if actuel <= cat.seuil_alerte:
            alertes_stock.append(f"{cat.nom}: {actuel} {cat.unite_mesure} (Seuil: {cat.seuil_alerte})")
        # Valeur estimée (simplifiée)
        if cat.nom.lower() in ['œuf', 'oeuf']:
            stock_valeur += actuel * 50  # Prix estimé par plateau
        elif cat.nom.lower() == 'provende':
            stock_valeur += actuel * 15000  # Prix estimé par sac
    
    # 👥 RESSOURCES
    batiments_actifs = Poulailler.objects.filter(effectif_initial__gt=0).count()
    total_batiments = Poulailler.objects.count()
    taux_occupation = round((batiments_actifs / total_batiments * 100), 1) if total_batiments > 0 else 0
    
    # 🚨 ALERTES DIRECTION (priorisées)
    alertes_direction = []
    if taux_mortalite > 2:
        alertes_direction.append({'niveau': 'critical', 'msg': f'🚨 Mortalité élevée : {taux_mortalite}% (Seuil: 2%)'})
    if taux_ponte_moy < 25:
        alertes_direction.append({'niveau': 'warning', 'msg': f'⚠️ Taux ponte bas : {taux_ponte_moy}% (Cible: >30%)'})
    if marge_brute < 0:
        alertes_direction.append({'niveau': 'critical', 'msg': '🚨 Marge négative ce mois-ci'})
    if alertes_stock:
        alertes_direction.append({'niveau': 'warning', 'msg': f'⚠️ {len(alertes_stock)} stock(s) critique(s)'})
    
    # 📊 DONNÉES GRAPHIQUES (CA 6 derniers mois)
    labels_ca, data_ca = [], []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year if today.month - i > 0 else today.year - 1
        ca = Vente.objects.filter(date__month=m, date__year=y).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
        labels_ca.append(f"{m:02d}/{y%100}")
        data_ca.append(ca // 1000)  # En milliers FCFA
    
    context = {
        # Financier
        'ca_mois': ca_mois, 'depenses_mois': depenses_mois, 
        'marge_brute': marge_brute, 'taux_marge': taux_marge,
        # Performance
        'total_oeufs': total_oeufs, 'taux_ponte_moy': round(taux_ponte_moy, 1),
        'taux_mortalite': taux_mortalite, 'cout_oeuf': cout_oeuf,
        # Stock
        'stock_valeur': stock_valeur, 'alertes_stock': alertes_stock,
        # Ressources
        'batiments_actifs': batiments_actifs, 'total_batiments': total_batiments,
        'taux_occupation': taux_occupation, 'effectif_total': effectif_total,
        # Alertes
        'alertes_direction': alertes_direction,
        # Graphiques
        'labels_ca': labels_ca, 'data_ca': data_ca,
        # Méta
        'period': '30 jours', 'today': today,
    }
    return render(request, 'gestion/dg_dashboard.html', context)
