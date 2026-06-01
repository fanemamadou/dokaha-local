from django.shortcuts import render, redirect
from datetime import datetime
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


@login_required
def credits_list(request):
    """Liste des créances clients impayées"""
    from .models import Vente
    from django.db.models import Sum
    from django.shortcuts import render
    creances = Vente.objects.filter(paye=False, montant_restant__gt=0).order_by('-date')
    total = creances.aggregate(total=Sum('montant_restant'))['total'] or 0
    return render(request, 'gestion/credits_list.html', {'creances': creances, 'total_credits': total})

@login_required
def credits_relance(request, vente_id):
    """Générer un message de relance pour un client"""
    from .models import Vente
    from django.shortcuts import get_object_or_404, render
    vente = get_object_or_404(Vente, pk=vente_id)
    msg = (f"Bonjour {vente.client},\n"
           f"Concernant votre achat du {vente.date.strftime('%d/%m/%Y')}:\n"
           f"📦 Total: {vente.montant_total:,.0f} FCFA | ✅ Déjà versé: {vente.montant_paye or 0:,.0f} FCFA\n"
           f"⚠️ *Reste à payer: {vente.montant_restant:,.0f} FCFA*\n\n"
           f"Merci de régulariser dans les meilleurs délais.\nCordialement, Dg Tropic 🇨🇮")
    return render(request, 'gestion/credits_relance.html', {'vente': vente, 'message': msg})

@login_required
def credits_payer(request, vente_id):
    """Marquer une créance comme réglée"""
    from .models import Vente
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    vente = get_object_or_404(Vente, pk=vente_id)
    vente.paye = True
    vente.montant_restant = 0
    vente.save()
    messages.success(request, f"✅ Créance de {vente.montant_total:,.0f} FCFA clôturée.")
    return redirect('credits_list')


@login_required
def credits_paiement_partiel(request, vente_id):
    """Gérer un paiement partiel ou total (avec Decimal pour éviter les erreurs)"""
    from .models import Vente
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    from decimal import Decimal

    vente = get_object_or_404(Vente, pk=vente_id)

    if request.method == 'POST':
        montant_str = request.POST.get('montant', '0')
        try:
            montant = Decimal(montant_str)
        except:
            messages.error(request, "❌ Montant invalide.")
            return redirect('credits_paiement', vente_id=vente_id)

        if montant <= 0:
            messages.error(request, "❌ Le montant doit être supérieur à 0.")
        elif montant > vente.montant_restant:
            messages.error(request, f"⚠️ Dépasse le reste dû ({vente.montant_restant:,.0f} F).")
        else:
            # ✅ Tous les calculs en Decimal
            vente.montant_paye = (vente.montant_paye or Decimal(0)) + montant
            vente.montant_restant = vente.montant_restant - montant
            
            if vente.montant_restant <= 0:
                vente.montant_restant = Decimal(0)
                vente.paye = True
            vente.save()
            
            msg = "✅ Créance totalement réglée !" if vente.paye else f"✅ Acompte de {int(montant)} F enregistré."
            messages.success(request, f"{msg} Reste: {int(vente.montant_restant)} FCFA")
            return redirect('credits_list')

    return render(request, 'gestion/credits_paiement.html', {'vente': vente})


@login_required
def finance_dashboard(request):
    from .models import Vente, Depense
    from django.db.models import Sum
    start, end = request.GET.get('start'), request.GET.get('end')
    qs_v, qs_d = Vente.objects.all(), Depense.objects.all()
    if start and end: qs_v, qs_d = qs_v.filter(date__range=[start, end]), qs_d.filter(date__range=[start, end])
    elif start: qs_v, qs_d = qs_v.filter(date__gte=start), qs_d.filter(date__gte=start)
    elif end: qs_v, qs_d = qs_v.filter(date__lte=end), qs_d.filter(date__lte=end)
    
    tr = int(qs_v.aggregate(t=Sum('montant_total'))['t'] or 0)
    td = int(qs_d.aggregate(t=Sum('montant'))['t'] or 0)
    
    labels, data = [], []
    for item in qs_v.values('type_vente').annotate(t=Sum('montant_total')).order_by('type_vente'):
        labels.append(item['type_vente']); data.append(int(item['t'] or 0))
        
    return render(request, 'gestion/finance_dashboard.html', {
        'total_recettes': tr, 'total_depenses': td, 'tresorerie': tr - td,
        'start_date': start or '', 'end_date': end or '',
        'chart_labels': labels, 'chart_data': data
    })

@login_required
def finance_export_excel(request):
    from .models import Vente, Depense
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    
    wb = openpyxl.Workbook()
    ws_r = wb.active; ws_r.title = "Recettes"
    ws_r.append(["Date", "Client", "Type", "Qté", "Prix", "Total", "Payé", "Reste"])
    for c in ws_r[1]: c.font = Font(bold=True); c.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    for v in Vente.objects.order_by('-date'):
        ws_r.append([v.date.strftime("%d/%m/%Y") if v.date else "", v.client or "", v.type_vente or "", int(v.unites or 0), int(v.prix_plateau or 0), int(v.montant_total or 0), int(v.montant_paye or 0), int(v.montant_restant or 0)])
    
    ws_d = wb.create_sheet("Dépenses")
    ws_d.append(["Date", "Catégorie", "Description", "Montant"])
    for c in ws_d[1]: c.font = Font(bold=True)
    for d in Depense.objects.order_by('-date'):
        ws_d.append([d.date.strftime("%d/%m/%Y") if d.date else "", d.categorie or "", d.description or "", int(d.montant or 0)])
        
    ws_rc = wb.create_sheet("Récap")
    ws_rc.append(["INDICATEUR", "VALEUR"]); ws_rc['A1'].font = Font(bold=True)
    tr = int(Vente.objects.aggregate(t=Sum('montant_total'))['t'] or 0)
    td = int(Depense.objects.aggregate(t=Sum('montant'))['t'] or 0)
    ws_rc.append(["Total Recettes", tr]); ws_rc.append(["Total Dépenses", td]); ws_rc.append(["Trésorerie", tr-td])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Tropic_Finance_{datetime.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response


@login_required
def cheptel(request):
    """Vue terrain : effectif réel par poulailler"""
    from .models import Poulailler, SortiePoules, Vente
    from django.db.models import Sum
    from django.shortcuts import render
    
    poulaillers = []
    for p in Poulailler.objects.all():
        effectif = p.effectif_initial or 0
        mortalite = SortiePoules.objects.filter(poulailler=p, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0
        ventes = Vente.objects.filter(poulailler=p, type_vente='poulets').aggregate(total=Sum('unites'))['total'] or 0
        effectif_reel = max(0, effectif - mortalite - int(ventes or 0))
        poulaillers.append({'nom': p.nom, 'initial': effectif, 'mortalite': int(mortalite or 0), 'vendus': int(ventes or 0), 'reel': effectif_reel, 'alerte': effectif_reel < (effectif * 0.8) if effectif > 0 else False})
    
    return render(request, 'gestion/cheptel.html', {'poulaillers': poulaillers, 'total_reel': sum(p['reel'] for p in poulaillers)})

@login_required
def terrain(request):
    """Interface terrain pour Flatie"""
    from .models import Poulailler, Vente, Depense, SortiePoules
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    from django.shortcuts import render

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    total_cheptel = Poulailler.objects.aggregate(total=Sum('effectif_initial'))['total'] or 0
    mortalite_week = SortiePoules.objects.filter(date__gte=week_ago, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0
    
    try:
        tr = Vente.objects.aggregate(t=Sum('montant_total'))['t'] or 0
        td = Depense.objects.aggregate(t=Sum('montant'))['t'] or 0
    except: tr = td = 0
    
    alerte_mortalite = mortalite_week > (total_cheptel * 0.02) if total_cheptel > 0 else False
    alerte_tresorerie = (tr - td) < 0
    
    activites = []
    try:
        for v in Vente.objects.order_by('-date')[:3]:
            activites.append({'date': v.date, 'type': 'Vente', 'detail': f"{v.type_vente} - {int(v.montant_total or 0)} F"})
        for m in SortiePoules.objects.filter(type_sortie='mortalite').order_by('-date')[:2]:
            activites.append({'date': m.date, 'type': 'Mortalité', 'detail': f"{int(m.nombre or 0)} sujets"})
        activites.sort(key=lambda x: x['date'] or today, reverse=True)
    except: pass
    
    return render(request, 'gestion/terrain.html', {
        'total_cheptel': total_cheptel, 'alerte_mortalite': alerte_mortalite,
        'alerte_tresorerie': alerte_tresorerie, 'activites_recentes': activites[:5]
    })

@login_required
def cheptel(request):
    """Vue terrain : effectif réel par poulailler"""
    from .models import Poulailler, SortiePoules, Vente
    from django.db.models import Sum
    from django.shortcuts import render
    
    poulaillers = []
    for p in Poulailler.objects.all():
        effectif = p.effectif_initial or 0
        mort = SortiePoules.objects.filter(poulailler=p, type_sortie='mortalite').aggregate(total=Sum('nombre'))['total'] or 0
        vend = Vente.objects.filter(poulailler=p, type_vente='poulets').aggregate(total=Sum('unites'))['total'] or 0
        reel = max(0, effectif - mort - int(vend or 0))
        poulaillers.append({'nom': p.nom, 'initial': effectif, 'mortalite': int(mort or 0), 'vendus': int(vend or 0), 'reel': reel, 'alerte': reel < (effectif * 0.8) if effectif > 0 else False})
    
    return render(request, 'gestion/cheptel.html', {'poulaillers': poulaillers, 'total_reel': sum(p['reel'] for p in poulaillers)})
