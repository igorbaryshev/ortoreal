from django import template

from inventory.utils import get_dec_display

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter
def dec(value):
    return get_dec_display(value)
