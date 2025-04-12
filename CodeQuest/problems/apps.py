from django.apps import AppConfig

class ProblemsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'problems'

    # def ready(self):
    #     # Import inside the method, to avoid triggering before app registry is ready
    #     from .elastic import create_index
    #     create_index()
