from django import template

register = template.Library()

@register.filter
def get_label(form, field_name):
    """
    Devuelve el label de un campo del formulario.
    Si no existe, retorna una cadena vacía.
    """
    try:
        return form.fields[field_name].label
    except KeyError:
        return ""
