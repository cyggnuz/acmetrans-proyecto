from django import forms
from .models import Solicitud
from django.core.exceptions import ValidationError
import re
from datetime import date


class SolicitudForm(forms.ModelForm):

    sucursal = forms.ChoiceField(
        choices=[('Santiago','Santiago'), ('Coquimbo','Coquimbo'), ('Osorno','Osorno')],
        required=True,
        label="Sucursal"
    )
    class Meta:
        model = Solicitud
        fields = [
            "nombre_cliente",
            "rut_cliente",
            "correo",
            "telefono",
            "direccion_retiro",
            "direccion_entrega",
            "fecha_retiro",
            "fecha_entrega",
            "tipo_carga",
            "peso_unidad",
            "peso_valor",
            "volumen_m2",
            "indicaciones_especiales",
        ]

        widgets = {
            "fecha_retiro": forms.DateInput(attrs={"type": "date"}),
            "fecha_entrega": forms.DateInput(attrs={"type": "date"}),
            "indicaciones_especiales": forms.Textarea(attrs={"rows": 3}),
        }

    # -------------------------------------
    # VALIDACIONES INDIVIDUALES
    # -------------------------------------

    def clean_nombre_cliente(self):
        nombre = self.cleaned_data["nombre_cliente"]
        if not re.match(r"^[A-Za-záéíóúÁÉÍÓÚñÑ ]{3,50}$", nombre):
            raise ValidationError("El nombre debe contener solo letras y mínimo 3 caracteres.")
        return nombre

    def clean_rut_cliente(self):
        rut = self.cleaned_data["rut_cliente"]
        rut = rut.replace(".", "").replace("-", "").upper()

        if not re.match(r"^\d{7,8}[0-9K]$", rut):
            raise ValidationError("Formato de RUT inválido. Ejemplo: 12345678K")

        return rut

    def clean_correo(self):
        correo = self.cleaned_data["correo"]
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,10}$", correo):
            raise ValidationError("Correo electrónico inválido.")
        return correo

    def clean_telefono(self):
        tel = self.cleaned_data["telefono"]
        tel_limpio = tel.replace(" ", "")
        if not re.match(r"^\+?56?9\d{8}$", tel_limpio):
            raise ValidationError("Teléfono inválido. Debe ser formato chileno: +569XXXXXXXX.")
        return tel

    def clean_direccion_retiro(self):
        d = self.cleaned_data["direccion_retiro"]
        if not re.match(r"^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ ,.#-]{5,100}$", d):
            raise ValidationError("Dirección inválida. Ej: 'Av. Siempre Viva 742, depto 10'")
        return d

    def clean_direccion_entrega(self):
        d = self.cleaned_data["direccion_entrega"]
        if not re.match(r"^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ ,.#-]{5,100}$", d):
            raise ValidationError("Dirección inválida. Ej: 'Av. Siempre Viva 742, depto 10'")
        return d

    def clean_peso_valor(self):
        p = self.cleaned_data["peso_valor"]
        if p < 100:
            raise ValidationError("El peso total debe ser al menos 100 kg.")
        return p

    # -------------------------------------
    # VALIDACIONES CRUZADAS
    # -------------------------------------
    def clean(self):
        cleaned = super().clean()

        fecha_retiro = cleaned.get("fecha_retiro")
        fecha_entrega = cleaned.get("fecha_entrega")

        hoy = date.today()

        if fecha_retiro and fecha_retiro < hoy:
            self.add_error("fecha_retiro", "La fecha de retiro no puede ser pasada.")

        if fecha_entrega and fecha_entrega < fecha_retiro:
            self.add_error("fecha_entrega", "La fecha de entrega no puede ser anterior a la de retiro.")

        return cleaned
