#!/usr/bin/env python3
"""
🥚 Import historique œufs - DOKAHA
Usage : python scripts/import_historique_oeufs.py --file data/oeufs_2024.csv --dry-run
"""
import os, sys, django, csv, argparse
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dokaha.settings')
sys.path.append('/home/fane/dokaha')
django.setup()

from gestion.models import ProductionOeufs, Vente, Poulailler, CategorieStock, MouvementStock
from django.contrib.auth.models import User

def load_poulaillers():
    """Cache des poulaillers par nom."""
    return {p.nom: p for p in Poulailler.objects.all()}

def get_user():
    """Utilisateur système pour les imports."""
    return User.objects.filter(is_superuser=True).first() or User.objects.first()

def import_production(filepath, dry_run=True, poulailler_default=None):
    """Importe les collectes historiques depuis CSV."""
    poulaillers = load_poulaillers()
    user = get_user()
    created = skipped = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                # Parsing des champs
                date_str = row.get('date') or row.get('Date')
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                nb_oeufs = int(row.get('nombre_oeufs') or row.get('Oeufs') or 0)
                casses = int(row.get('oeufs_casses') or row.get('Casses') or 0)
                poulailler_nom = row.get('poulailler') or row.get('Bâtiment') or poulailler_default
                
                poulailler = poulaillers.get(poulailler_nom) if poulailler_nom else None
                
                # Vérifier doublon
                if ProductionOeufs.objects.filter(date=date, poulailler=poulailler, nombre_oeufs=nb_oeufs).exists():
                    skipped += 1
                    continue
                
                if not dry_run:
                    ProductionOeufs.objects.create(
                        date=date, poulailler=poulailler,
                        nombre_oeufs=nb_oeufs, oeufs_casses=casses,
                        
                    )
                created += 1
                
                if i % 1000 == 0:
                    print(f"  → Ligne {i}: {created} créés, {skipped} ignorés")
                    
            except Exception as e:
                print(f"⚠️ Ligne {i} ignorée : {e}")
                continue
    
    action = "SIMULÉ (dry-run)" if dry_run else "ENREGISTRÉ"
    print(f"\n✅ Import production : {created} nouveaux, {skipped} doublons ignorés [{action}]")
    return created

def import_ventes(filepath, dry_run=True):
    """Importe les ventes historiques d'œufs depuis CSV."""
    user = get_user()
    created = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                date_str = row.get('date') or row.get('Date')
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                quantite = float(row.get('quantite') or row.get('Plateaux') or 0)
                prix = float(row.get('prix') or row.get('Prix') or 0)
                client = row.get('client') or row.get('Client') or 'Historique'
                
                if not dry_run:
                    Vente.objects.create(
                        date=date, client=client, type_vente='oeufs',
                        plateaux=quantite, prix_unitaire=prix,
                        montant_total=float(quantite or 0) * float(prix or 0), paye=True,
                        
                    )
                created += 1
                
            except Exception as e:
                print(f"⚠️ Vente ligne {i} ignorée : {e}")
                continue
    
    action = "SIMULÉ (dry-run)" if dry_run else "ENREGISTRÉ"
    print(f"\n✅ Import ventes : {created} ventes [{action}]")
    return created

def verify_stock():
    from django.db.models import Sum
    total_produit = ProductionOeufs.objects.aggregate(Sum('nombre_oeufs'))['nombre_oeufs__sum'] or 0
    try:
        raw = Vente.objects.filter(type_vente='oeufs').aggregate(Sum('plateaux'))['plateaux__sum']
        total_plateaux = float(raw) if raw else 0.0
    except:
        total_plateaux = 0.0
    stock_calc = int(total_produit - (total_plateaux * 30))
    print('')
    print('📊 État stock Œufs :')
    print('   • Total collecté : {:,} œufs'.format(total_produit))
    print('   • Total vendu : {:,.1f} plateaux (~{:,} œufs)'.format(total_plateaux, int(total_plateaux*30)))
    print('   • Stock théorique : {:,} œufs'.format(stock_calc))
    try:
        cat = CategorieStock.objects.get(nom__in=['Œufs', 'Oeufs'])
        print('   ✅ Catégorie stock trouvée : ' + cat.nom)
    except:
        print('   ⚠️ Catégorie Œufs absente de CategorieStock')
    print('')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='🥚 Import historique œufs')
    parser.add_argument('--file', '-f', required=True, help='Chemin du CSV')
    parser.add_argument('--type', '-t', choices=['production', 'vente', 'all'], default='production')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Simulation sans écriture')
    parser.add_argument('--poulailler', '-p', help='Poulailler par défaut si absent du CSV')
    args = parser.parse_args()
    
    print(f"🚀 Démarrage import {'(DRY-RUN) ' if args.dry_run else ''}depuis {args.file}")
    
    if args.type in ['production', 'all']:
        import_production(args.file, dry_run=args.dry_run, poulailler_default=args.poulailler)
    if args.type in ['vente', 'all']:
        import_ventes(args.file, dry_run=args.dry_run)
    
    verify_stock()
    print("\n✨ Terminé.")
