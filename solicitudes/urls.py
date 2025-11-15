from django.urls import path
from . import views

urlpatterns = [
    # Página principal pública de clientes
    path('cliente/solicitud/', views.solicitud_cliente, name='solicitud_cliente'),

    # Crear solicitud (para secretaria o admin)
    path('solicitudes/nueva/', views.crear_solicitud, name='crear_solicitud'),

    # Detalle y acciones sobre una solicitud
    path('solicitudes/<int:pk>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitudes/<int:pk>/simular/', views.simular_avance, name='simular_avance'),
    path('solicitudes/<int:pk>/aprobar/', views.aprobar, name='aprobar'),
    path('solicitudes/<int:pk>/rechazar/', views.rechazar, name='rechazar'),


    # RUTAS DEL PANEL ADMIN
    path('panel/', views.panel_admin, name='panel_admin'),
    path('inbox/', views.inbox, name='inbox'),
    path('panel/solicitudes/', views.panel_solicitudes, name='solicitudes'),
    path('panel/reportes/', views.reportes, name='reportes'),

    # Historial dentro del panel
    path('panel/historial/', views.panel_historial, name='historial'),

    path('reportes/resumen/', views.reporte_resumen, name='reporte_resumen'),
    path("reportes/pdf/", views.generar_resumen_pdf, name="generar_resumen_pdf"),


]
