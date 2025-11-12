from django import forms
from .models import Solicitud

class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = [
            "nombre_cliente",
            "rut_cliente",
            "tipo_carga",
            "peso_valor",
            "peso_unidad",
            "volumen_m2",
            "fecha_retiro",
            "fecha_entrega",
            "direccion_retiro",
            "direccion_entrega",
            "indicaciones_especiales",
        ]
        labels = {
            "nombre_cliente": "Nombre de la empresa",
            "rut_cliente": "RUT de la empresa",
            "tipo_carga": "Tipo de carga",
            "peso_valor": "Peso",
            "peso_unidad": "Unidad de peso",
            "volumen_m2": "Volumen (m²)",
            "fecha_retiro": "Fecha de retiro de la carga",
            "fecha_entrega": "Fecha de entrega de la carga",
            "direccion_retiro": "Dirección de retiro",
            "direccion_entrega": "Dirección de entrega",
            "indicaciones_especiales": "Indicaciones especiales",
        }
        widgets = {
            "nombre_cliente": forms.TextInput(attrs={
                "placeholder": "Ingrese nombre"
            }),
            "rut_cliente": forms.TextInput(attrs={
                "placeholder": "Ingrese RUT"
            }),
            "tipo_carga": forms.Select(),
            "peso_valor": forms.NumberInput(attrs={
                "placeholder": "Ingrese peso",
                "step": "0.01"
            }),
            "peso_unidad": forms.Select(),
            "volumen_m2": forms.NumberInput(attrs={
                "placeholder": "Ingrese volumen (m²)",
                "step": "0.01"
            }),
            "fecha_retiro": forms.DateInput(attrs={"type": "date"}),
            "fecha_entrega": forms.DateInput(attrs={"type": "date"}),
            "direccion_retiro": forms.TextInput(attrs={
                "placeholder": "Ingrese dirección de retiro"
            }),
            "direccion_entrega": forms.TextInput(attrs={
                "placeholder": "Ingrese dirección de entrega"
            }),
            "indicaciones_especiales": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Ingrese indicaciones"
            }),
        }
