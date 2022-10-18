from django import template

register = template.Library()

@register.filter
def price(value):
    if value != "0":
        return "{:.2f}".format(float(value) / 100)
    else:
        return 0

@register.filter
def datefield(value):
    return str(value)
