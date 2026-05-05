from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender='gestion.ProductionOeufs')
def auto_stock_entree_oeufs(sender, instance, created, **kwargs):
    """Collecte → entrée stock automatique."""
    if not created:
        return
    try:
        from .models import CategorieStock, MouvementStock
        cat = CategorieStock.objects.filter(nom__in=['Œufs', 'Oeufs']).first()
        if not cat:
            return
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            return
        MouvementStock.objects.get_or_create(
            categorie=cat, date=instance.date, quantite=instance.nombre_oeufs,
            type_mouvement='entree',
            defaults={'fournisseur_client': f"Collecte auto", 'cree_par': user}
        )
    except Exception:
        pass  # Échec silencieux pour ne pas bloquer

@receiver(post_save, sender='gestion.Vente')
def auto_stock_sortie_oeufs(sender, instance, created, **kwargs):
    """Vente d'œufs → sortie stock automatique (1 plateau = 30 œufs)."""
    if not created or instance.type_vente != 'oeufs':
        return
    try:
        from .models import CategorieStock, MouvementStock
        cat = CategorieStock.objects.filter(nom__in=['Œufs', 'Oeufs']).first()
        if not cat:
            return
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            return
        # Conversion plateaux → œufs (ajuste le facteur si besoin)
        quantite_oeufs = int(instance.plateaux * 30)
        MouvementStock.objects.get_or_create(
            categorie=cat, date=instance.date, quantite=quantite_oeufs,
            type_mouvement='sortie',
            defaults={'fournisseur_client': f"Vente auto ({instance.client})", 'cree_par': user}
        )
    except Exception:
        pass
