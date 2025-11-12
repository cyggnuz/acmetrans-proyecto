from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SolicitudesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'solicitudes'
    verbose_name = 'Gestión de Solicitudes'

    def ready(self):
        # Conecta la función que creará los grupos tras las migraciones
        post_migrate.connect(create_default_groups, sender=self)


def create_default_groups(sender, **kwargs):
    """Crea los grupos base 'Director' y 'Secretaria' si no existen."""
    from django.contrib.auth.models import Group 

    grupos = ['Director', 'Secretaria']

    for nombre in grupos:
        grupo, creado = Group.objects.get_or_create(name=nombre)
        if creado:
            print(f'✅ Grupo creado automáticamente: {nombre}')
        else:
            print(f'ℹ️ Grupo existente: {nombre}')
