from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings
from django.db import models
from django.utils import timezone

class Poulailler(models.Model):
    nom = models.CharField(max_length=100, default="")
    effectif_initial = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.nom

class ProductionOeufs(models.Model):
    date = models.DateField(default=timezone.now)
    poulailler = models.ForeignKey(Poulailler, on_delete=models.CASCADE)
    nombre_oeufs = models.IntegerField()
    oeufs_casses = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.date} - {self.nombre_oeufs} œufs"

class Vente(models.Model):
    poulailler = models.ForeignKey(Poulailler, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bâtiment")
    date = models.DateField(verbose_name="Date")
    client = models.CharField(max_length=100, blank=True, null=True, verbose_name="Client")
    type_vente = models.CharField(
        max_length=20,
        choices=[('oeufs', '🥚 Œufs'), ('poules', '🐔 Poules'), ('autres', '📦 Autres')],
        default='oeufs'
    )
    plateaux = models.IntegerField(default=0)
    unites = models.IntegerField(default=0)
    prix_plateau = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paye = models.BooleanField(default=True)
    # 💳 Champs paiements (DOIVENT correspondre à la DB)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant payé (FCFA)")
    montant_restant = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Reste à payer (FCFA)")
    mode_paiement = models.CharField(
        max_length=20,
        default='comptant',
        choices=[('comptant', '💵 Comptant'), ('credit', '📝 Crédit'), ('mobile', '📱 Mobile Money'), ('cheque', '🧾 Chèque')],
        verbose_name="Mode de paiement"
    )

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-date']

    def __str__(self):
        return f"{self.client or 'Inconnu'} - {self.montant_total} FCFA"

    def save(self, *args, **kwargs):
        # Auto-calcul du statut payé
        self.paye = (self.montant_paye >= self.montant_total)
        super().save(*args, **kwargs)



    
    def clean(self):
        # Empêcher payé > total
        if self.montant_paye and self.montant_total and self.montant_paye > self.montant_total:
            from django.core.exceptions import ValidationError
            raise ValidationError("Le montant payé ne peut pas dépasser le total.")
        # Auto-calcul du statut payé
        self.paye = (self.montant_paye or 0) >= (self.montant_total or 0)

class Depense(models.Model):
    date = models.DateField(default=timezone.now)
    categorie = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, default="")
    def __str__(self):
        return f"{self.date} - {self.categorie}"

class SortiePoules(models.Model):
    date = models.DateField(default=timezone.now)
    poulailler = models.ForeignKey(Poulailler, on_delete=models.CASCADE)
    nombre = models.PositiveIntegerField()
    TYPE_CHOICES = [('mortalite', '🪦 Mortalité'), ('vente', '💰 Vente improductive')]
    type_sortie = models.CharField(max_length=20, choices=TYPE_CHOICES)
    prix_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    def __str__(self):
        return f"{self.date} - {self.nombre} {self.type_sortie}"

class LotPoules(models.Model):
    nom = models.CharField(max_length=100, default="")
    date_arrivee = models.DateField()
    effectif = models.IntegerField(default=0)
    def __str__(self):
        return self.nom

class Client(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, default="")
    def __str__(self):
        return self.nom

class Sante(models.Model):
    date = models.DateField(default=timezone.now)
    poulailler = models.ForeignKey(Poulailler, on_delete=models.CASCADE)
    traitement = models.CharField(max_length=200)
    def __str__(self):
        return f"{self.date} - {self.poulailler}"

class MouvementCheptel(models.Model):
    TYPES = [
        ('achat', '🛒 Achat / Renouvellement'),
        ('transfert_in', '📥 Transfert entrant'),
        ('transfert_out', '📤 Transfert sortant'),
        ('reforme', '🔄 Réforme / Vente cheptel'),
        ('mortalite', '🪦 Mortalité exceptionnelle'),
    ]
    date = models.DateField()
    poulailler = models.ForeignKey('Poulailler', on_delete=models.PROTECT, related_name='mouvements_cheptel')
    type_mouvement = models.CharField(max_length=20, choices=TYPES)
    nombre_poules = models.IntegerField(help_text="Nombre de poules concernées")
    commentaire = models.TextField(blank=True, null=True, help_text="Ex: Lot acheté à X, transfert Bât. C...")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Mouvement de cheptel"
        verbose_name_plural = "Mouvements de cheptel"

    def __str__(self):
        return f"{self.get_type_mouvement_display()} → {self.poulailler.nom} ({self.nombre_poules} p.) le {self.date}"


# 📦 MODULE STOCK - 30/04/2026
# 📦 MODULE STOCK (Définitions propres et uniques)
class CategorieStock(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    unite_mesure = models.CharField(max_length=20)
    seuil_alerte = models.PositiveIntegerField()
    actif = models.BooleanField(default=True, verbose_name='Actif / Visible formulaire stock')

    class Meta:
        verbose_name = "Catégorie de stock"
        ordering = ['nom']
    def __str__(self): return f"{self.nom} ({self.unite_mesure})"
    def stock_actuel(self):
        e = self.mouvements.filter(type_mouvement='entree').aggregate(t=Sum('quantite'))['t'] or 0
        s = self.mouvements.filter(type_mouvement__in=['sortie','perte']).aggregate(t=Sum('quantite'))['t'] or 0
        return e - s
    def est_critique(self): return self.stock_actuel() <= self.seuil_alerte


class Produit(models.Model):
    categorie = models.ForeignKey(CategorieStock, on_delete=models.CASCADE, related_name="produits")
    nom = models.CharField(max_length=100, unique=True)
    unite = models.CharField(max_length=20, default="unités")
    seuil_alerte = models.IntegerField(default=0, help_text="Quantité minimum déclenchant une alerte")
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.unite})"

    @property
    def stock_actuel(self):
        # Calcul temps réel : Entrées - Sorties + Ajustements
        entrees = self.mouvements.filter(type_mvt='ENTREE').aggregate(total=models.Sum('quantite'))['total'] or 0
        sorties = self.mouvements.filter(type_mvt='SORTIE').aggregate(total=models.Sum('quantite'))['total'] or 0
        ajustements = self.mouvements.filter(type_mvt='AJUSTEMENT').aggregate(total=models.Sum('quantite'))['total'] or 0
        return entrees - sorties + ajustements

    class Meta:
        verbose_name = "Produit / Article"
        verbose_name_plural = "Produits"
        ordering = ['categorie', 'nom']

class MouvementStock(models.Model):
    TYPE = [('entree','📥 Entrée'),('sortie','📤 Sortie'),('ajustement','🔧'),('perte','🗑️')]
    categorie = models.ForeignKey(CategorieStock, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    type_mouvement = models.CharField(max_length=20, choices=TYPE)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, editable=False)
    fournisseur_client = models.CharField(max_length=200, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    commentaire = models.TextField(blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    class Meta:
        verbose_name = "Mouvement de stock"
        ordering = ['-date']
    def save(self, *a, **k):
        if self.quantite and self.prix_unitaire: self.montant_total = self.quantite * self.prix_unitaire
        super().save(*a, **k)
    def __str__(self): return f"{self.categorie.nom if self.categorie else 'N/A'} - {self.quantite}"

class AlertesStock(models.Model):
    categorie = models.ForeignKey(CategorieStock, on_delete=models.CASCADE)
    date_alerte = models.DateTimeField(auto_now_add=True)
    niveau = models.CharField(max_length=20, choices=[('warning','⚠️'),('critical','🚨')])
    message = models.TextField()
    acquittee = models.BooleanField(default=False)
    date_acquittement = models.DateTimeField(null=True, blank=True)
    acquittee_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        verbose_name = "Alerte stock"
        ordering = ['-date_alerte']
    def __str__(self): return f"{self.categorie.nom} - {self.niveau}"
