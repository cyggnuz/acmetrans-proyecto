from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def home_redirect(request):
    """
    Redirige al usuario a la vista correspondiente según su rol (grupo).
    - Director → panel_director
    - Secretaria → crear_solicitud
    """
    if request.user.groups.filter(name='Director').exists():
        return redirect('panel_director')

    elif request.user.groups.filter(name='Secretaria').exists():
        return redirect('crear_solicitud')

    else:
        # Si el usuario no pertenece a ningún grupo, se le muestra un aviso y se cierra la sesión
        messages.warning(request, "No tiene un rol asignado. Contacte al administrador.")
        return redirect('logout')
