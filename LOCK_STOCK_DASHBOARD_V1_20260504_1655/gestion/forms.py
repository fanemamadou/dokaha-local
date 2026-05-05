from decimal import Decimal
from django import forms
from .models import Produit,  ProductionOeufs, MouvementStock, CategorieStock

# 🥚 Formulaire collecte œufs (inchangé)
class ProductionOeufsForm(forms.ModelForm):
    class Meta:
        model = ProductionOeufs
        fields = ['poulailler', 'date', 'nombre_oeufs', 'oeufs_casses']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre_oeufs': forms.NumberInput(attrs={'class': 'form-control'}),
            'oeufs_casses': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# 📦 Formulaire mouvement stock BASE
class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['categorie', 'date', 'quantite', 'prix_unitaire', 'fournisseur_client', 'reference', 'commentaire']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fournisseur_client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Agro-CI, Pharmavet...'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# 📥 Formulaire ENTRÉE : exclut les œufs de production (filtre robuste)
class StockEntreeForm(MouvementStockForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclure toute catégorie contenant "oeuf" (case-insensitive) SAUF si c'est un emballage
        # On exclut uniquement la catégorie exacte de production d'œufs
        qs = CategorieStock.objects.all()
        # Astuce : on exclut par ID si on connaît l'ID de la catégorie Œufs
        egg_cats = [c.id for c in qs if c.nom.strip().lower() in ['œufs', 'oeufs', 'oeuf', 'œuf']]
        if egg_cats:
            self.fields['categorie'].queryset = qs.exclude(id__in=egg_cats)
        self.fields['prix_unitaire'].required = False

# 📤 Formulaire SORTIE : même logique
class StockSortieForm(MouvementStockForm):
    class Meta(MouvementStockForm.Meta):
        fields = ['categorie', 'date', 'quantite', 'fournisseur_client', 'commentaire']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = CategorieStock.objects.all()
        egg_cats = [c.id for c in qs if c.nom.strip().lower() in ['œufs', 'oeufs', 'oeuf', 'œuf']]
        if egg_cats:
            self.fields['categorie'].queryset = qs.exclude(id__in=egg_cats)
        if 'prix_unitaire' in self.fields:
            self.fields['prix_unitaire'].widget = forms.HiddenInput()


# 📦 Formulaire Mouvement Stock
# 📦 Formulaire Mouvement Stock (Catégorie + Choices réels)
# 📦 Formulaire Mouvement Stock (Catégorie + Choices réels)
class StockMouvementForm(forms.Form):
    categorie = forms.ModelChoiceField(
        queryset=CategorieStock.objects.all().order_by('nom'),
        label='Catégorie de stock',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    type_mouvement = forms.ChoiceField(
        choices=[('entree', '📥 Entrée'), ('sortie', '📤 Sortie'), ('ajustement', '🔧 Ajustement'), ('perte', '🗑️ Perte')],
        label='Type de mouvement',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantite = forms.DecimalField(
        min_value=Decimal('0.01'), max_digits=10, decimal_places=2,
        label='Quantité',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 100.00'})
    )
    commentaire = forms.CharField(
        required=False,
        label='Commentaire (optionnel)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motif du mouvement...'})
    )