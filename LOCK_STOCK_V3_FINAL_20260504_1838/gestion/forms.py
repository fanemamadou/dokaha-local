from django import forms
from .models import CategorieStock, MouvementStock

# 📦 Formulaire Mouvement Stock (version finale)
class StockMouvementForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['categorie', 'type_mouvement', 'quantite', 'commentaire']
        widgets = {
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔒 FILTRE STRICT : Ne montre que les catégories où actif=True
        # Comme Œufs est à False en base, il disparaîtra automatiquement.
        self.fields['categorie'].queryset = CategorieStock.objects.filter(actif=True).order_by('nom')

    def clean_quantite(self):
        q = self.cleaned_data.get('quantite')
        if q and q <= 0:
            raise forms.ValidationError("La quantité doit être > 0")
        return q

# 📦 Placeholders pour compatibilité avec views.py
class StockEntreeForm(StockMouvementForm):
    pass

class StockSortieForm(StockMouvementForm):
    pass
