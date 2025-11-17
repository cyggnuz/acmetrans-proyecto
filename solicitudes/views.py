from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import random
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from .models import Solicitud
from .forms import SolicitudForm
from django.contrib.auth import logout
import matplotlib
matplotlib.use('Agg')



# ============================
# LISTAS VALIDAS
# ============================

SUCURSALES_VALIDAS = ["Santiago", "Coquimbo", "Osorno"]
TIPOS_CARGA_VALIDOS = ["General", "Refrigerada", "Peligrosa", "Maquinaria Pesada", "Granel"]


# ============================
# SUCURSAL ACTIVA (VALIDADA)
# ============================

def get_sucursal(request):
    suc = request.GET.get("sucursal")

    if suc == "todas":
        request.session["sucursal_activa"] = None
        return None

    if suc not in SUCURSALES_VALIDAS:
        return request.session.get("sucursal_activa", None)

    request.session["sucursal_activa"] = suc
    return suc


# ============================
# ROLES
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
# HOME
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

            suc = request.POST.get("sucursal")
            if suc not in SUCURSALES_VALIDAS:
                suc = "Santiago"
            sol.sucursal = suc

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
        "pendientes": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Pendiente").count() if sucursal_activa else Solicitud.objects.filter(estado="Pendiente").count(),
        "proceso": Solicitud.objects.filter(sucursal=sucursal_activa, estado="En proceso").count() if sucursal_activa else Solicitud.objects.filter(estado="En proceso").count(),
        "finalizadas": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Finalizada").count() if sucursal_activa else Solicitud.objects.filter(estado="Finalizada").count(),
        "rechazadas": Solicitud.objects.filter(sucursal=sucursal_activa, estado="Rechazada").count() if sucursal_activa else Solicitud.objects.filter(estado="Rechazada").count(),
    }

    solicitudes = (
        Solicitud.objects.filter(sucursal=sucursal_activa)
        if sucursal_activa else Solicitud.objects.all()
    ).order_by("-fecha_creacion")

    total_solicitudes = solicitudes.count()

    return render(request, "panel_director.html", {
        "resumen": resumen,
        "solicitudes": solicitudes,
        "total_solicitudes": total_solicitudes,
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
        {"id": 1, "titulo": "Transporte completado", "hora": "09:45 AM", "detalle": f"Camión llegó a {sucursal_activa or 'todas las sucursales'}."},
        {"id": 2, "titulo": "Nueva solicitud", "hora": "10:10 AM", "detalle": "Solicitud recibida."},
        {"id": 3, "titulo": "Estado actualizado", "hora": "11:00 AM", "detalle": "Una solicitud pasó a 'En proceso'."},
    ]

    return render(request, "inbox.html", {
        "notificaciones": notificaciones,
        "active": "inbox",
        "sucursal_activa": sucursal_activa
    })


# ============================
# PANEL DE SOLICITUDES
# ============================

@login_required
@user_passes_test(solo_director)
def panel_solicitudes(request):

    sucursal_activa = get_sucursal(request)

    if sucursal_activa:
        solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa)
    else:
        solicitudes = Solicitud.objects.all()

    solicitudes = solicitudes.order_by('-fecha_creacion')

    resumen = {
        'pendientes': solicitudes.filter(estado='Pendiente').count(),
        'proceso': solicitudes.filter(estado='En proceso').count(),
        'finalizadas': solicitudes.filter(estado='Finalizada').count(),
        'rechazadas': solicitudes.filter(estado='Rechazada').count(),
    }

    total_solicitudes = solicitudes.count()

    return render(request, "solicitudes.html", {
        "solicitudes": solicitudes,
        "resumen": resumen,
        "total_solicitudes": total_solicitudes,
        "sucursal_activa": sucursal_activa,
        "SUCURSALES": [(s, s) for s in SUCURSALES_VALIDAS],
        "active": "solicitudes"
    })


# ============================
# DETALLE SOLICITUD
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
# SIMULAR, APROBAR, RECHAZAR
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
    return redirect('historial')


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
    return redirect('historial')


# ============================
# HISTORIAL
# ============================

@login_required
@user_passes_test(solo_director)
def panel_historial(request):

    sucursal_activa = get_sucursal(request)

    if sucursal_activa:
        historial = Solicitud.objects.filter(sucursal=sucursal_activa)
    else:
        historial = Solicitud.objects.all()

    historial = historial.exclude(estado__in=['Pendiente', 'En proceso']).order_by('-fecha_cierre')

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

            suc = request.POST.get("sucursal")
            if suc not in SUCURSALES_VALIDAS:
                suc = "Santiago"
            sol.sucursal = suc

            tipo_post = request.POST.get("tipo_carga")
            if tipo_post not in TIPOS_CARGA_VALIDOS:
                tipo_post = "General"
            sol.tipo_carga = tipo_post

            if sol.fecha_entrega < sol.fecha_retiro:
                messages.error(request, "La fecha de entrega no puede ser anterior a la fecha de retiro.")
                return redirect("solicitud_cliente")

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
# REPORTES
# ============================

@login_required
@user_passes_test(solo_director)
def reportes(request):

    sucursal_activa = get_sucursal(request)

    if sucursal_activa in SUCURSALES_VALIDAS:
        solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa)
    else:
        solicitudes = Solicitud.objects.all()

    resumen = {
        "pendientes": solicitudes.filter(estado="Pendiente").count(),
        "en_proceso": solicitudes.filter(estado="En proceso").count(),
        "finalizadas": solicitudes.filter(estado="Finalizada").count(),
        "rechazadas": solicitudes.filter(estado="Rechazada").count(),
    }

    total_solicitudes = solicitudes.count()

    # Gráfico áreas
    area_operaciones = solicitudes.filter(estado="Pendiente").count()
    area_direccion = solicitudes.filter(estado="En proceso").count()
    area_finanzas = solicitudes.filter(estado__in=["Finalizada", "Rechazada"]).count()

    grafico_areas = {
        "labels": ["Operaciones", "Dirección", "Finanzas"],
        "data": [area_operaciones, area_direccion, area_finanzas]
    }

    return render(request, "reportes.html", {
        "resumen": resumen,
        "total_solicitudes": total_solicitudes,
        "active": "reportes",
        "sucursal_activa": sucursal_activa,
        "grafico_areas": grafico_areas,
    })


# ============================
# REPORTE PDF
# ============================

@login_required
@user_passes_test(solo_director)
def generar_resumen_pdf(request):

    sucursal_activa = request.session.get("sucursal_activa", "Santiago")
    solicitudes = Solicitud.objects.filter(sucursal=sucursal_activa)

    # Resumen por estado
    resumen = {
        "pendientes": solicitudes.filter(estado="Pendiente").count(),
        "en_proceso": solicitudes.filter(estado="En proceso").count(),
        "finalizadas": solicitudes.filter(estado="Finalizada").count(),
        "rechazadas": solicitudes.filter(estado="Rechazada").count(),
    }

    total = solicitudes.count()

    secciones = {
        "Operaciones": resumen["pendientes"],
        "Dirección": resumen["en_proceso"],
        "Finanzas": resumen["finalizadas"] + resumen["rechazadas"],
    }

    # =============================
    # GRÁFICO 1: DONUT (estados)
    # =============================
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64

    def generar_grafico_donut():
        fig, ax = plt.subplots(figsize=(4, 4))
        labels = list(resumen.keys())
        valores = list(resumen.values())
        colores = ['#f1c40f', '#3498db', '#2ecc71', '#e74c3c']
        ax.pie(valores, labels=labels, autopct='%1.1f%%', colors=colores)
        ax.axis("equal")

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        imagen = base64.b64encode(buffer.read()).decode()
        plt.close()
        return imagen

    grafico_donut = generar_grafico_donut()

    # =============================
    # GRÁFICO 2: BARRAS (secciones)
    # =============================
    def generar_grafico_barras():
        fig, ax = plt.subplots(figsize=(5, 4))

        labels = list(secciones.keys())
        valores = list(secciones.values())

        ax.bar(labels, valores, color=['#9b59b6','#2980b9','#27ae60'])
        ax.set_title("Solicitudes por Sección")
        ax.set_ylabel("Cantidad")

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        imagen = base64.b64encode(buffer.read()).decode()
        plt.close()
        return imagen

    grafico_barras = generar_grafico_barras()

    # Enviar a la plantilla
    context = {
        "solicitudes": solicitudes,
        "resumen": resumen,
        "secciones": secciones,
        "total": total,
        "sucursal": sucursal_activa,
        "fecha": timezone.now().date(),
        "grafico_donut": grafico_donut,
        "grafico_barras": grafico_barras,
    }

    html_string = render_to_string("reporte_pdf.html", context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_acme.pdf"'

    return response



# ============================
# FINALIZAR SOLICITUD
# ============================

@login_required
@user_passes_test(solo_director)
def finalizar_solicitud(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk)
    solicitud.estado = "Finalizada"
    solicitud.save()
    return redirect('panel_admin')


# ============================ # MOTIVOS RECHAZO # ============================
@login_required
@user_passes_test(solo_director)
def rechazar(request, pk):

    s = get_object_or_404(Solicitud, pk=pk)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "No especificado")

        s.estado = 'Rechazada'
        s.estado_final = 'Rechazada'
        s.motivo_cierre = motivo
        s.fecha_cierre = timezone.now().date()
        s.save()

        messages.warning(request, f"Solicitud {s.id_solicitud} rechazada.")
        return redirect('solicitudes')

    return redirect('solicitudes')

# ============================
# LOGOUT
# ============================

def logout_view(request):
    logout(request)
    return redirect('login')
