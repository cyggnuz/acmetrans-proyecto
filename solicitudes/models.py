from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags
import bleach

ESTADOS = [
    ('Pendiente', 'Pendiente'),
    ('En proceso', 'En proceso'),
    ('Finalizada', 'Finalizada'),
    ('Rechazada', 'Rechazada'),
]

SUCURSALES = [
    ('Santiago', 'Santiago'),
    ('Coquimbo', 'Coquimbo'),
    ('Osorno', 'Osorno'),
]

TIPO_CARGA = [
    ('General', 'General'),
    ('Refrigerada', 'Refrigerada'),
    ('Peligrosa', 'Peligrosa'),
    ('Maquinaria Pesada', 'Maquinaria Pesada'),
    ('Granel', 'Granel'),
]

UNIDADES_PESO = [
    ('kg', 'Kilogramos (kg)'),
    ('ton', 'Toneladas (ton)'),
]


#   MEDIDA DE SEGURIDAD 1:
#   Sanitización de texto

def clean_input(texto):
    """
    Limpia entradas de texto para evitar:
    - HTML Injection
    - XSS
    - JavaScript embebido
    - Etiquetas HTML maliciosas
    """
    if not texto:
        return ""
    
    # strip_tags elimina cualquier etiqueta HTML
    limpio = strip_tags(texto)

    # bleach.clean elimina scripts, eventos onClick, etc.
    limpio = bleach.clean(
        limpio,
        tags=[],           # No permitir ninguna etiqueta HTML
        attributes={},     
        strip=True         
    )

    return limpio


class Solicitud(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Identificación
    id_solicitud = models.CharField(max_length=30, unique=True, editable=False, blank=True)
    sucursal = models.CharField(max_length=20, choices=SUCURSALES, default='Santiago')

    # FORMULARIO 
    nombre_cliente     = models.CharField(max_length=120)
    rut_cliente        = models.CharField(max_length=20)

    correo             = models.CharField(max_length=120)
    telefono           = models.CharField(max_length=20)

    volumen_m2         = models.FloatField(help_text="Volumen en metros cuadrados (m²)")
    peso_valor         = models.FloatField(help_text="Valor del peso según unidad seleccionada")
    peso_unidad        = models.CharField(max_length=3, choices=UNIDADES_PESO, default='kg')

    fecha_retiro       = models.DateField()
    fecha_entrega      = models.DateField()

    direccion_retiro   = models.CharField(max_length=200)
    direccion_entrega  = models.CharField(max_length=200)

    tipo_carga         = models.CharField(max_length=30, choices=TIPO_CARGA)
    indicaciones_especiales = models.TextField(blank=True, null=True)

    # Estado general
    estado = models.CharField(max_length=40, choices=ESTADOS, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # --- Simulación Operaciones / Finanzas ---
    recursos_necesarios     = models.CharField(max_length=200, blank=True)
    tiempo_viaje_estimado   = models.CharField(max_length=120, blank=True)
    costo_combustible_clp   = models.IntegerField(blank=True, null=True)
    costo_personal_clp      = models.IntegerField(blank=True, null=True)
    costo_peajes_clp        = models.IntegerField(blank=True, null=True)
    permisos_especiales_clp = models.IntegerField(blank=True, null=True)
    riesgo_logistico        = models.CharField(max_length=40, blank=True)
    accion_pendiente        = models.CharField(max_length=120, blank=True)

    # Cierre / Historial
    estado_final  = models.CharField(max_length=20, blank=True)
    motivo_cierre = models.CharField(max_length=200, blank=True)
    fecha_cierre  = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.id_solicitud} · {self.nombre_cliente}"

    # Helper para normalizar a kg
    def peso_en_kg(self) -> float:
        return self.peso_valor * 1000 if self.peso_unidad == 'ton' else self.peso_valor

    #   Limpiar texto antes de guardar

    def save(self, *args, **kwargs):
        # Generar ID único solo si no existe
        if not self.id_solicitud:
            self.id_solicitud = f"SOL-{datetime.now().strftime('%Y%m%d')}-{get_random_string(5).upper()}"

        # Sanitización de campos críticos
        self.nombre_cliente = clean_input(self.nombre_cliente)
        self.rut_cliente = clean_input(self.rut_cliente)
        self.direccion_retiro = clean_input(self.direccion_retiro)
        self.direccion_entrega = clean_input(self.direccion_entrega)
        self.indicaciones_especiales = clean_input(self.indicaciones_especiales)

        # Validación segura de sucursal (anti-manipulación)
        if self.sucursal not in ["Santiago", "Coquimbo", "Osorno"]:
            self.sucursal = "Santiago"

        super().save(*args, **kwargs)

MOTIVOS_RECHAZO = [
    ("Precio no competitivo", "Precio no competitivo"),
    ("Capacidad logística insuficiente", "Capacidad logística insuficiente"),
    ("Documentación incompleta", "Documentación incompleta"),
    ("Información inconsistente", "Información inconsistente"),
    ("Ruta no disponible", "Ruta no disponible"),
]
