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
    """Dashboard: KPIs + Actions + Activité Récente"""
    from .models import Poulailler, Vente, Depense, SortiePoules
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    from django.shortcuts import render

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    total_cheptel = Poulailler.objects.aggregate(total=Sum('effectif_initial'))['total'] or 0
    mortalite_today = SortiePoules.objects.filter(date=today, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0
    mortalite_week = SortiePoules.objects.filter(date__gte=week_ago, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0

    try:
        total_recettes = Vente.objects.aggregate(total=Sum('montant_total'))['total'] or 0
        total_depenses = Depense.objects.aggregate(total=Sum('montant'))['total'] or 0
    except:
        total_recettes = 0
        try: total_depenses = Depense.objects.aggregate(total=Sum('montant_total'))['total'] or 0
        except: total_depenses = 0

    tresorerie = total_recettes - total_depenses
    alerte_mortalite = mortalite_week > (total_cheptel * 0.02) if total_cheptel > 0 else False
    alerte_tresorerie = tresorerie < 0

    # 📜 Activité Récente (mix Ventes + Mortalités)
    activites = []
    try:
        for v in Vente.objects.order_by('-date')[:3]:
            activites.append({'date': v.date, 'type': '💰 Vente', 'detail': f"{v.type_vente} - {v.montant_total:,.0f} F", 'info': v.client or 'N/A'})
        for m in SortiePoules.objects.filter(type_sortie='mortalite').order_by('-date')[:2]:
            activites.append({'date': m.date, 'type': '💀 Mortalité', 'detail': f"{m.nombre} sujets", 'info': 'Cheptel'})
        activites.sort(key=lambda x: x['date'], reverse=True)
        activites = activites[:5]
    except:
        activites = []

    return render(request, 'gestion/dashboard.html', {
        'total_cheptel': total_cheptel, 'mortalite_today': mortalite_today,
        'mortalite_week': mortalite_week, 'tresorerie': tresorerie,
        'alerte_mortalite': alerte_mortalite, 'alerte_tresorerie': alerte_tresorerie,
        'activites_recentes': activites
    })


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
    """Formulaire vente unifié : oeufs/poulets/autres + déduction sécurisée"""
    from .models import Vente, Poulailler
    from django.contrib import messages
    from django.utils import timezone
    from django.shortcuts import redirect
    from django.db import transaction

    poulaillers = Poulailler.objects.all()

    if request.method == 'POST':
        client = request.POST.get('client', '').strip()
        unites = float(request.POST.get('unites', 0) or 0)
        prix = float(request.POST.get('prix', 0) or 0)
        montant_paye = float(request.POST.get('montant_paye', 0) or 0)
        mode_paiement = request.POST.get('mode_paiement', 'espece')
        poulailler_id = request.POST.get('poulailler_id')
        designation = request.POST.get('designation', '').strip()

        if not client or unites <= 0 or prix <= 0:
            messages.error(request, "❌ Client, quantité et prix obligatoires.")
        elif type_vente == 'autres' and not designation:
            messages.error(request, "❌ Désignation obligatoire pour ce type.")
        else:
            try:
                with transaction.atomic():
                    montant_total = unites * prix
                    montant_restant = max(0, montant_total - montant_paye)
                    paye = montant_restant == 0
                    msg = ""

                    # 🐔 Déduction poulailler pour poulets
                    if type_vente == 'poulets' and poulailler_id:
                        p = Poulailler.objects.select_for_update().get(id=poulailler_id)
                        if p.effectif_initial < unites:
                            raise ValueError(f"⚠️ Effectif insuffisant dans {p.nom} ({p.effectif_initial} dispo)")
                        p.effectif_initial -= int(unites)
                        p.save()
                        msg = f"🐔 Déduit de {p.nom} | "

                    Vente.objects.create(
                        date=timezone.now().date(), client=client, type_vente=type_vente,
                        unites=unites, prix_plateau=prix, montant_total=montant_total,
                        montant_paye=montant_paye, montant_restant=montant_restant,
                        paye=paye, mode_paiement=mode_paiement,
                        poulailler_id=poulailler_id if type_vente == 'poulets' else None
                    )
                    messages.success(request, f"✅ Vente validée ! {msg}Total: {montant_total:,.0f} FCFA")
                    return redirect('dashboard')
            except Poulailler.DoesNotExist:
                messages.error(request, "❌ Poulailler introuvable.")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"❌ Erreur: {e}")

    return render(request, 'gestion/vente_form.html', {
        'type_vente': type_vente, 'poulaillers': poulaillers, 'now': timezone.now()
    })


@login_required
def acces_refuse(request):
    return render(request, 'gestion/acces_refuse.html', {'title': '🚫 Accès Refusé', 'user': request.user})

# 📦 VUES STOCK - Ajoutées proprement (ne pas toucher)
@login_required
def stock_historique(request):
    return render(request, 'gestion/base.html', {'title': '📜 Historique Stock', 'user': request.user})
@login_required
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
@login_required
def stock_dashboard(request):
    """Dashboard Stock V2 : indicateurs visuels + ratios"""
    from django.db.models import Sum
    from gestion.models import CategorieStock, MouvementStock

    categories = CategorieStock.objects.all().order_by('nom')
    data = []
    total_alertes = 0
    
    for cat in categories:
        entrees = MouvementStock.objects.filter(categorie=cat, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
        sorties = MouvementStock.objects.filter(categorie=cat, type_mouvement='sortie').aggregate(Sum('quantite'))['quantite__sum'] or 0
        ajust   = MouvementStock.objects.filter(categorie=cat, type_mouvement='ajustement').aggregate(Sum('quantite'))['quantite__sum'] or 0
        pertes  = MouvementStock.objects.filter(categorie=cat, type_mouvement='perte').aggregate(Sum('quantite'))['quantite__sum'] or 0
        
        stock = float(entrees - sorties + ajust - pertes)
        seuil = cat.seuil_alerte or 0
        is_critical = seuil > 0 and stock <= seuil
        if is_critical: total_alertes += 1
        
        # Ratio pour barre de progression (max 100%)
        ratio = min(100, round((stock / seuil * 100) if seuil > 0 else 0, 1))
        
        data.append({
            'cat': cat, 'stock': stock, 'seuil': seuil,
            'is_critical': is_critical, 'ratio': ratio
        })
        
    return render(request, 'gestion/stock_dashboard.html', {
        'title': '📦 État des Stocks',
        'categories': data,
        'total_categories': len(data),
        'total_alertes': total_alertes,
        'user': request.user
    })

# 🥚 VUE COLLECTE ŒUFS (DUAL MODE + SYNC STOCK)
@login_required
def collecte_oeufs(request):
    """Formulaire collecte œufs : mode Plateaux ou Vrac + mouvement stock auto"""
    from .forms import ProductionOeufsForm
    from .models import MouvementStock, CategorieStock
    from django.contrib import messages
    from decimal import Decimal
    
    cat_oeufs = CategorieStock.objects.filter(nom__icontains='oeuf').first()
    
    if request.method == 'POST':
        form = ProductionOeufsForm(request.POST)
        if form.is_valid():
            collecte = form.save(user=request.user)
            
            # Créer mouvement stock si catégorie Œufs existe
            if cat_oeufs and collecte.nombre_oeufs > 0:
                MouvementStock.objects.create(
                    categorie=cat_oeufs,
                    date=collecte.date,
                    type_mouvement='entree',
                    quantite=Decimal(str(collecte.nombre_oeufs)),
                    commentaire=f'Collecte: {collecte.plateaux} plateaux + {collecte.reste_oeufs} œufs',
                    cree_par=request.user
                )
                msg = f"✅ {collecte.plateaux} plateaux + {collecte.reste_oeufs} œufs = {collecte.nombre_oeufs} œufs enregistrés + stock mis à jour"
            else:
                msg = f"✅ {collecte.nombre_oeufs} œufs enregistrés"
            
            messages.success(request, msg)
            return redirect('/collecte/')
    else:
        form = ProductionOeufsForm()
    
    return render(request, 'gestion/collecte_oeufs.html', {
        'form': form, 'title': '🥚 Collecte Œufs', 'user': request.user
    })



@login_required
def mortalite_form(request):
    from .forms import MortaliteForm
    from .models import Poulailler, SortiePoules
    from django.db.models import Sum
    from django.utils import timezone
    from django.contrib import messages

    # Préparer les données du tableau
    poulaillers_data = []
    for p in Poulailler.objects.all():
        m = SortiePoules.objects.filter(poulailler=p, type_sortie='mortalite').aggregate(t=Sum('nombre'))['t'] or 0
        poulaillers_data.append({'nom': p.nom, 'initial': p.effectif_initial, 'mortalites': m, 'reste': p.effectif_initial - m})

    if request.method == 'POST':
        form = MortaliteForm(request.POST)
        if form.is_valid():
            p = form.cleaned_data['poulailler']
            n = form.cleaned_data['nombre']
            if n <= p.effectif_initial:
                p.effectif_initial -= n
                p.save()
                SortiePoules.objects.create(date=form.cleaned_data['date'], poulailler=p, nombre=n, type_sortie='mortalite')
                messages.success(request, f"✅ {n} poules déduites de '{p.nom}'")
                return redirect('mortalite_form')
            else:
                messages.error(request, f"⚠️ Effectif insuffisant ({p.effectif_initial} < {n})")
    else:
        form = MortaliteForm(initial={'date': timezone.now().date()})

    return render(request, 'gestion/mortalite_form.html', {'form': form, 'poulaillers': poulaillers_data})


@login_required
def dashboard(request):
    """Dashboard: KPIs + Actions + Activité Récente"""
    from .models import Poulailler, Vente, Depense, SortiePoules
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    from django.shortcuts import render

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    total_cheptel = Poulailler.objects.aggregate(total=Sum('effectif_initial'))['total'] or 0
    mortalite_today = SortiePoules.objects.filter(date=today, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0
    mortalite_week = SortiePoules.objects.filter(date__gte=week_ago, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0

    try:
        total_recettes = Vente.objects.aggregate(total=Sum('montant_total'))['total'] or 0
        total_depenses = Depense.objects.aggregate(total=Sum('montant'))['total'] or 0
    except:
        total_recettes = 0
        try: total_depenses = Depense.objects.aggregate(total=Sum('montant_total'))['total'] or 0
        except: total_depenses = 0

    tresorerie = total_recettes - total_depenses
    alerte_mortalite = mortalite_week > (total_cheptel * 0.02) if total_cheptel > 0 else False
    alerte_tresorerie = tresorerie < 0

    # 📜 Activité Récente (mix Ventes + Mortalités)
    activites = []
    try:
        for v in Vente.objects.order_by('-date')[:3]:
            activites.append({'date': v.date, 'type': '💰 Vente', 'detail': f"{v.type_vente} - {v.montant_total:,.0f} F", 'info': v.client or 'N/A'})
        for m in SortiePoules.objects.filter(type_sortie='mortalite').order_by('-date')[:2]:
            activites.append({'date': m.date, 'type': '💀 Mortalité', 'detail': f"{m.nombre} sujets", 'info': 'Cheptel'})
        activites.sort(key=lambda x: x['date'], reverse=True)
        activites = activites[:5]
    except:
        activites = []

    return render(request, 'gestion/dashboard.html', {
        'total_cheptel': total_cheptel, 'mortalite_today': mortalite_today,
        'mortalite_week': mortalite_week, 'tresorerie': tresorerie,
        'alerte_mortalite': alerte_mortalite, 'alerte_tresorerie': alerte_tresorerie,
        'activites_recentes': activites
    })

