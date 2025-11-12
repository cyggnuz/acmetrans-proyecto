from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class UsernameOrEmailBackend(ModelBackend):
    """
    Permite autenticación con username o email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Buscar por username o email
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        # Verifica contraseña
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
