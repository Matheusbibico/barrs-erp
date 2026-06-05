from django.apps import AppConfig


class PedidosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pedidos'
    verbose_name = 'Pedidos'

    def ready(self):
        import pedidos.signals  # noqa: F401
