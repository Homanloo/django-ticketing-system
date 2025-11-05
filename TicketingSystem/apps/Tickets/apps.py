from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Tickets'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.Tickets.signals