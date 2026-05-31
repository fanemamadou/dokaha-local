from django import forms
from .models import Poulailler, CategorieStock, MouvementStock, ProductionOeufs

# 📦 Formulaire Mouvement Stock (version stable)
class StockMouvementForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['categorie', 'type_mouvement', 'quantite', 'commentaire']
        widgets = {
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔒 FILTRE : Ne montre que les catégories où actif=True
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


# 🥚 Formulaire Collecte Œufs (version minimale - champs garantis)
class ProductionOeufsForm(forms.ModelForm):
    class Meta:
        model = ProductionOeufs
        fields = ['poulailler', 'date', 'nombre_oeufs']
        widgets = {
            'poulailler': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nombre_oeufs': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()


class MortaliteForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    poulailler = forms.ModelChoiceField(queryset=Poulailler.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    nombre = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
