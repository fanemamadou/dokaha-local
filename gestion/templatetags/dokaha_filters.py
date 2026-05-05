from django import template
register = template.Library()

@register.filter(name='sum_list')
def sum_list(value):
    """Somme les éléments d'une liste"""
    try:
        return sum(float(v) for v in value)
    except:
        return 0

@register.filter(name='mul')
def mul(value, arg):
    """Multiplication : value * arg"""
    try:
        return float(value) * float(arg)
    except:
        return value

@register.filter(name='zip_lists')
def zip_lists(a, b):
    """Zip deux listes pour itération parallèle"""
    return list(zip(a, b))
