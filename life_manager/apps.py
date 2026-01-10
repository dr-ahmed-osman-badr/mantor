from django.apps import AppConfig


class LifeManagerConfig(AppConfig):
    name = 'life_manager'

    def ready(self):
        import life_manager.signals
