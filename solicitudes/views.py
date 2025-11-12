from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
import random
from .models import Solicitud
from .forms import SolicitudForm
from django.contrib.auth import logout

# ================================
# VISTA DE INICIO
# ================================
def home_page(request):
    """Página de inicio para clientes, secretaria y administrador."""
    if request.user.is_authenticated:
        return home_redirect(request)
    return render(request, 'home.html')


# ================================
# FUNCIONES AUXILIARES DE ROLES
# ================================
def es_admin(user):
    """Verifica si el usuario es superusuario."""
    return user.is_superuser

def es_director(user):
    """Verifica si el usuario pertenece al grupo 'Director' o es admin."""
    return user.is_superuser or user.groups.filter(name='Director').exists()

def es_secretaria(user):
    """Verifica si el usuario pertenece al grupo 'Secretaria' o es admin."""
    return user.is_superuser or user.groups.filter(name='Secretaria').exists()


# ================================
# REDIRECCIÓN SEGÚN ROL
# ================================
@login_required
def home_redirect(request):
    """Redirige al usuario según su grupo o si es admin."""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            messages.info(request, "Bienvenido Administrador General.")
            return redirect('panel_director')
        elif request.user.groups.filter(name='Director').exists():
            return redirect('panel_director')
        elif request.user.groups.filter(name='Secretaria').exists():
            return redirect('crear_solicitud')
        else:
            messages.warning(request, "No tiene un rol asignado. Contacte al administrador.")
            return redirect('logout')
    return redirect('login')


# ================================
# VISTAS PARA SECRETARIA
# ================================
@login_required
@user_passes_test(es_secretaria)
def crear_solicitud(request):
    """Permite a la secretaria o admin crear una nueva solicitud."""
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            sol = form.save(commit=False)
            sol.estado = 'Pendiente'
            sol.save()
            messages.success(request, "Solicitud ingresada exitosamente.")
            return render(request, 'solicitud_ok.html', {"solicitud": sol})
    else:
        form = SolicitudForm()
    return render(request, 'formulario_solicitud.html', {"form": form})


# ================================
# VISTAS PARA DIRECTOR / ADMIN
# ================================
@login_required
@user_passes_test(es_director)
def panel_director(request):
    """Panel principal del director o administrador con filtro por estado y sucursal."""
    filtro_estado = request.GET.get('estado', 'Pendiente')
    sucursal_activa = request.GET.get('sucursal', 'Santiago')

    solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa).order_by('-fecha_creacion')

    if filtro_estado in ['Pendiente', 'En proceso', 'Finalizada', 'Rechazada']:
        solicitudes = solicitudes.filter(estado=filtro_estado)

    resumen = {
        'pendientes': Solicitud.objects.filter(estado='Pendiente').count(),
        'proceso': Solicitud.objects.filter(estado='En proceso').count(),
        'finalizadas': Solicitud.objects.filter(estado='Finalizada').count(),
        'rechazadas': Solicitud.objects.filter(estado='Rechazada').count(),
    }

    return render(request, 'panel_director.html', {
        "solicitudes": solicitudes,
        "filtro": filtro_estado,
        "resumen": resumen,
        "sucursal_activa": sucursal_activa,
    })


@login_required
@user_passes_test(es_director)
def detalle_solicitud(request, pk):
    sol = get_object_or_404(Solicitud, pk=pk)
    return render(request, 'detalle_solicitud.html', {"s": sol})


@login_required
@user_passes_test(es_director)
def simular_avance(request, pk):
    s = get_object_or_404(Solicitud, pk=pk)
    peso_kg = s.peso_en_kg()

    s.recursos_necesarios = "2 Camiones MC" if peso_kg > 15000 else "1 Camión"
    origen = s.direccion_retiro.split(',')[0] if s.direccion_retiro else "Origen"
    destino = s.direccion_entrega.split(',')[0] if s.direccion_entrega else "Destino"
    s.tiempo_viaje_estimado = f"4 días ({origen} → {destino})"

    s.costo_combustible_clp = random.randint(1800000, 2500000)
    s.costo_personal_clp = 1200000
    s.costo_peajes_clp = random.choice([300000, 450000, 500000])
    s.permisos_especiales_clp = 750000 if s.tipo_carga == "Peligrosa" else 0
    s.riesgo_logistico = "Medio" if s.tipo_carga == "Peligrosa" else "Bajo"
    s.accion_pendiente = "Cálculo de Utilidad y Precio Final"
    s.estado = 'En proceso'
    s.save()

    messages.info(request, f"Se simuló Operaciones/Finanzas para {s.id_solicitud}.")
    return redirect('detalle_solicitud', pk=s.pk)


@login_required
@user_passes_test(es_director)
def aprobar(request, pk):
    s = get_object_or_404(Solicitud, pk=pk)
    s.estado = 'Finalizada'
    s.estado_final = 'Aceptada'
    s.motivo_cierre = 'Servicio Finalizado y Pagado'
    s.fecha_cierre = timezone.now().date()
    s.save()

    messages.success(request, f"Solicitud {s.id_solicitud} aceptada.")
    return redirect('historial')


@login_required
@user_passes_test(es_director)
def rechazar(request, pk):
    s = get_object_or_404(Solicitud, pk=pk)
    s.estado = 'Rechazada'
    s.estado_final = 'Rechazada'
    s.motivo_cierre = 'Precio no competitivo'
    s.fecha_cierre = timezone.now().date()
    s.save()

    messages.warning(request, f"Solicitud {s.id_solicitud} rechazada.")
    return redirect('historial')


@login_required
@user_passes_test(es_director)
def historial(request):
    cerradas = Solicitud.objects.exclude(
        estado__in=['Pendiente', 'En proceso']
    ).order_by('-fecha_cierre', '-fecha_creacion')
    return render(request, 'historial.html', {"solicitudes": cerradas})


# ================================
# FORMULARIO PÚBLICO (CLIENTE)
# ================================
def solicitud_cliente(request):
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            sol = form.save(commit=False)
            sol.estado = 'Pendiente'
            sol.save()
            messages.success(request, "Su solicitud fue enviada exitosamente.")
            return render(request, 'solicitud_ok.html', {"solicitud": sol})
    else:
        form = SolicitudForm()
    return render(request, 'solicitud_cliente.html', {"form": form})


# ================================
# SECCIONES DEL PANEL
# ================================
def inbox(request):
    notificaciones = [
        {"id": 1, "titulo": "Transporte completado", "hora": "09:45 AM", "detalle": "Camión #102 llegó a Coquimbo."},
        {"id": 2, "titulo": "Nueva solicitud recibida", "hora": "10:10 AM", "detalle": "Cliente: María López (Osorno)."},
        {"id": 3, "titulo": "Solicitud actualizada", "hora": "11:00 AM", "detalle": "Solicitud #A234 pasó a 'En Proceso'."},
    ]
    return render(request, "inbox.html", {"notificaciones": notificaciones, "active": "inbox"})


@login_required
@user_passes_test(es_director)
def panel_solicitudes(request):
    solicitudes = Solicitud.objects.all().order_by('-fecha_creacion')
    resumen = {
        'pendientes': solicitudes.filter(estado='Pendiente').count(),
        'proceso': solicitudes.filter(estado='En proceso').count(),
        'finalizadas': solicitudes.filter(estado='Finalizada').count(),
        'rechazadas': solicitudes.filter(estado='Rechazada').count(),
    }
    return render(request, "solicitudes.html", {
        "solicitudes": solicitudes,
        "resumen": resumen,
        "active": "solicitudes"
    })


@login_required
@user_passes_test(es_director)
def panel_admin(request):
    resumen = {
        "pendientes": Solicitud.objects.filter(estado="Pendiente").count(),
        "proceso": Solicitud.objects.filter(estado="En proceso").count(),
        "finalizadas": Solicitud.objects.filter(estado="Finalizada").count(),
        "rechazadas": Solicitud.objects.filter(estado="Rechazada").count(),
    }
    solicitudes = Solicitud.objects.all().order_by("-fecha_creacion")[:5]
    return render(request, "panel.html", {
        "resumen": resumen,
        "solicitudes": solicitudes,
        "filtro": "Pendiente",
        "sucursal_activa": "Santiago",
    })

@login_required
@user_passes_test(es_director)
def reportes(request):
    """Vista de reportes básicos del sistema."""
    resumen = {
        "pendientes": Solicitud.objects.filter(estado="Pendiente").count(),
        "en_proceso": Solicitud.objects.filter(estado="En proceso").count(),
        "finalizadas": Solicitud.objects.filter(estado="Finalizada").count(),
        "rechazadas": Solicitud.objects.filter(estado="Rechazada").count(),
    }

    total_solicitudes = Solicitud.objects.count()

    return render(request, "reportes.html", {
        "resumen": resumen,
        "total_solicitudes": total_solicitudes,
        "active": "reportes",
    })


@login_required
@user_passes_test(es_director)
def panel_historial(request):
    """Vista del historial de solicitudes finalizadas o rechazadas."""
    historial = Solicitud.objects.exclude(estado__in=['Pendiente', 'En proceso']).order_by('-fecha_cierre')

    return render(request, "historial.html", {
        "solicitudes": historial,
        "active": "historial",
    })


def logout_view(request):
    logout(request)
    return redirect('login')