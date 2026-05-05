#!/usr/bin/env python3
"""
🥚 Sync rétroactive : ProductionOeufs → MouvementStock
Usage : python scripts/sync_historique_stock.py --dry-run  # puis sans --dry-run pour appliquer
"""
import os, sys, django, argparse
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dokaha.settings')
sys.path.append('/home/fane/dokaha')
django.setup()

from gestion.models import ProductionOeufs, CategorieStock, MouvementStock
from django.contrib.auth.models import User
from django.db.models import Q

def sync_historique(dry_run=True, batch_size=100):
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not user:
        print("❌ Aucun utilisateur trouvé pour cree_par")
        return
    
    # Trouver la catégorie Œufs
    cat = CategorieStock.objects.filter(Q(nom='Œufs') | Q(nom='Oeufs')).first()
    if not cat:
        print("❌ Catégorie 'Œufs' introuvable dans CategorieStock")
        print("💡 Crée-la d'abord via /stock/categories/ ou l'admin")
        return
    
    # Trouver les ProductionOeufs SANS MouvementStock correspondant
    # On compare par (date, poulailler, nombre_oeufs) pour éviter les doublons
    created = skipped = 0
    
    print(f"🔍 Recherche des collectes sans entrée stock...")
    
    for prod in ProductionOeufs.objects.all().order_by('date'):
        # Vérifier si un mouvement équivalent existe déjà
        exists = MouvementStock.objects.filter(
            categorie=cat,
            date=prod.date,
            quantite=prod.nombre_oeufs,
            type_mouvement='entree'
        ).exists()
        
        if exists:
            skipped += 1
            continue
        
        if not dry_run:
            MouvementStock.objects.create(
                categorie=cat,
                date=prod.date,
                quantite=prod.nombre_oeufs,
                type_mouvement='entree',
                fournisseur_client=f"Historique auto ({prod.poulailler.nom if prod.poulailler else 'N/A'})",
                commentaire=f"Sync rétroactive depuis ProductionOeufs #{prod.id}",
                cree_par=user
            )
        created += 1
        
        if created % 1000 == 0:
            print(f"  → {created} créés, {skipped} ignorés...")
    
    action = "SIMULÉ (dry-run)" if dry_run else "✅ ENREGISTRÉ en base"
    print(f"\n📊 Résultat : {created} entrées stock créées, {skipped} déjà existantes [{action}]")
    
    # Afficher le nouveau total stock
    from django.db.models import Sum
    total_mvt = MouvementStock.objects.filter(categorie=cat, type_mouvement='entree').aggregate(Sum('quantite'))['quantite__sum'] or 0
    print(f"📦 Stock Œufs dans MouvementStock : {total_mvt:,} œufs")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', '-d', action='store_true', help='Simulation sans écriture')
    args = parser.parse_args()
    
    print(f"🚀 Sync rétroactive {'(DRY-RUN) ' if args.dry_run else ''}en cours...")
    sync_historique(dry_run=args.dry_run)
    print("✨ Terminé.")
