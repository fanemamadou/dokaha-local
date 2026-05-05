from django.apps import AppConfig

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'
    
    def ready(self):
        # Charger les signaux uniquement quand Django est prêt
        from . import signals  # noqa
