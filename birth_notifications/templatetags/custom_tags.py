from django import template

register = template.Library()

@register.filter
def price(value):
    return "{:.2f}".format(float(value) / 100)

@register.filter
def datefield(value):
    return str(value)
