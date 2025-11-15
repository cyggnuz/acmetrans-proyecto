from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.html import strip_tags

import random
from .models import Solicitud
from .forms import SolicitudForm
from django.contrib.auth import logout

# ============================
# LISTAS VALIDAS PARA VALIDACIÓN
# ============================

SUCURSALES_VALIDAS = ["Santiago", "Coquimbo", "Osorno"]
TIPOS_CARGA_VALIDOS = ["General", "Refrigerada", "Peligrosa", "Maquinaria Pesada", "Granel"]


# ============================
# SUCURSAL ACTIVA CON VALIDACIÓN
# ============================

def get_sucursal(request):

    suc = request.GET.get("sucursal")

    # Si el usuario intenta manipularlo manualmente, se corrige automáticamente
    if suc not in SUCURSALES_VALIDAS:
        return request.session.get("sucursal_activa", "Santiago")

    # Se guarda la sucursal en sesión
    request.session["sucursal_activa"] = suc
    return suc


# ============================
# REGLAS DE ROLES
# ============================

def es_director(user):
    return user.is_superuser or user.groups.filter(name='Director').exists()

def es_secretaria(user):
    return user.is_superuser or user.groups.filter(name='Secretaria').exists()

def solo_director(user):
    if not es_director(user):
        raise PermissionDenied
    return True

def solo_secretaria(user):
    if not es_secretaria(user):
        raise PermissionDenied
    return True


# ============================
# HOME & REDIRECCIONES
# ============================

def home_page(request):
    if request.user.is_authenticated:
        return home_redirect(request)
    return render(request, 'home.html')


@login_required
def home_redirect(request):

    if es_director(request.user):
        return redirect('panel_admin')

    if es_secretaria(request.user):
        return redirect('crear_solicitud')

    messages.warning(request, "No tiene un rol asignado.")
    return redirect('logout')


# ============================
# SECRETARIA: CREAR SOLICITUD
# ============================

@login_required
@user_passes_test(solo_secretaria)
def crear_solicitud(request):

    if request.method == 'POST':
        form = SolicitudForm(request.POST)

        if form.is_valid():
            sol = form.save(commit=False)

            # Validación de sucursal
            suc = request.POST.get("sucursal")
            if suc not in SUCURSALES_VALIDAS:
                suc = "Santiago"
            sol.sucursal = suc

            # Sanitizar campos de texto largo
            sol.indicaciones_especiales = strip_tags(sol.indicaciones_especiales or "")

            sol.estado = 'Pendiente'
            sol.save()

            messages.success(request, "Solicitud ingresada exitosamente.")
            return render(request, 'solicitud_ok.html', {"solicitud": sol})

    else:
        form = SolicitudForm()

    return render(request, 'formulario_solicitud.html', {
        "form": form,
        "active": "solicitudes"
    })


# ============================
# PANEL DIRECTOR
# ============================

@login_required
@user_passes_test(solo_director)
def panel_admin(request):

    sucursal_activa = get_sucursal(request)

    resumen = {
        "pendientes": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Pendiente").count(),
        "proceso": Solicitud.objects.filter(sucursal=sucursal_activa, estado="En proceso").count(),
        "finalizadas": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Finalizada").count(),
        "rechazadas": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Rechazada").count(),
    }

    solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa).order_by("-fecha_creacion")[:5]

    return render(request, "panel_director.html", {
        "resumen": resumen,
        "solicitudes": solicitudes,
        "sucursal_activa": sucursal_activa,
        "active": "panel"
    })


# ============================
# INBOX
# ============================

@login_required
@user_passes_test(solo_director)
def inbox(request):

    sucursal_activa = get_sucursal(request)

    notificaciones = [
        {"id": 1, "titulo": "Transporte completado", "hora": "09:45 AM", "detalle": f"Camión llegó a {sucursal_activa}."},
        {"id": 2, "titulo": "Nueva solicitud", "hora": "10:10 AM", "detalle": f"Solicitud recibida en {sucursal_activa}."},
        {"id": 3, "titulo": "Estado actualizado", "hora": "11:00 AM", "detalle": "Una solicitud pasó a 'En proceso'."},
    ]

    return render(request, "inbox.html", {
        "notificaciones": notificaciones,
        "active": "inbox",
        "sucursal_activa": sucursal_activa
    })


# ============================
# PANEL SOLICITUDES
# ============================

@login_required
@user_passes_test(solo_director)
def panel_solicitudes(request):

    sucursal_activa = get_sucursal(request)
    solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa).order_by('-fecha_creacion')

    resumen = {
        'pendientes': solicitudes.filter(estado='Pendiente').count(),
        'proceso': solicitudes.filter(estado='En proceso').count(),
        'finalizadas': solicitudes.filter(estado='Finalizada').count(),
        'rechazadas': solicitudes.filter(estado='Rechazada').count(),
    }

    return render(request, "solicitudes.html", {
        "solicitudes": solicitudes,
        "resumen": resumen,
        "sucursal_activa": sucursal_activa,
        "active": "solicitudes"
    })


# ============================
# DETALLE
# ============================

@login_required
@user_passes_test(solo_director)
def detalle_solicitud(request, pk):

    sol = get_object_or_404(Solicitud, pk=pk)

    return render(request, 'detalle_solicitud.html', {
        "s": sol,
        "active": "solicitudes"
    })


# ============================
# SIMULAR / APROBAR / RECHAZAR
# ============================

@login_required
@user_passes_test(solo_director)
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
    messages.info(request, f"Se simuló para {s.id_solicitud}.")
    return redirect('detalle_solicitud', pk=s.pk)


@login_required
@user_passes_test(solo_director)
def aprobar(request, pk):

    s = get_object_or_404(Solicitud, pk=pk)
    s.estado = 'Finalizada'
    s.estado_final = 'Aceptada'
    s.motivo_cierre = 'Servicio Finalizado y Pagado'
    s.fecha_cierre = timezone.now().date()
    s.save()

    messages.success(request, f"Solicitud {s.id_solicitud} aceptada.")
    return redirect('panel_historial')


@login_required
@user_passes_test(solo_director)
def rechazar(request, pk):

    s = get_object_or_404(Solicitud, pk=pk)
    s.estado = 'Rechazada'
    s.estado_final = 'Rechazada'
    s.motivo_cierre = 'Precio no competitivo'
    s.fecha_cierre = timezone.now().date()
    s.save()

    messages.warning(request, f"Solicitud {s.id_solicitud} rechazada.")
    return redirect('panel_historial')


# ============================
# HISTORIAL
# ============================

@login_required
@user_passes_test(solo_director)
def panel_historial(request):

    sucursal_activa = get_sucursal(request)

    historial = Solicitud.objects.filter(
        sucursal=sucursal_activa
    ).exclude(
        estado__in=['Pendiente', 'En proceso']
    ).order_by('-fecha_cierre')

    return render(request, "historial.html", {
        "solicitudes": historial,
        "active": "historial",
        "sucursal_activa": sucursal_activa
    })


# ============================
# FORMULARIO PÚBLICO
# ============================

def solicitud_cliente(request):

    if request.method == 'POST':
        form = SolicitudForm(request.POST)

        if form.is_valid():
            sol = form.save(commit=False)

            # Validación sucursal
            suc = request.POST.get("sucursal")
            if suc not in SUCURSALES_VALIDAS:
                suc = "Santiago"
            sol.sucursal = suc

            # Validación tipo de carga
            tipo_post = request.POST.get("tipo_carga")
            if tipo_post not in TIPOS_CARGA_VALIDOS:
                tipo_post = "General"
            sol.tipo_carga = tipo_post

            # Validación fecha
            if sol.fecha_entrega < sol.fecha_retiro:
                messages.error(request, "La fecha de entrega no puede ser anterior a la fecha de retiro.")
                return redirect("solicitud_cliente")

            # Sanitizar campo largo
            sol.indicaciones_especiales = strip_tags(sol.indicaciones_especiales or "")

            sol.estado = 'Pendiente'
            sol.id_solicitud = f"S{random.randint(10000,99999)}"
            sol.save()

            messages.success(request, "Solicitud enviada.")
            return render(request, 'solicitud_ok.html', {"solicitud": sol})
    else:
        form = SolicitudForm()

    return render(request, 'solicitud_cliente.html', {"form": form})


# ============================
# LOGOUT
# ============================

def logout_view(request):
    logout(request)
    return redirect('login')
