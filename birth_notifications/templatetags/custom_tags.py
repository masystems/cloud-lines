from django import template

register = template.Library()


@register.filter
def get_living_births(value):
    count = 0
    for birth in value.births.all():
        if birth.status == 'alive':
            count += 1
    return count

@register.filter
def get_deceased_births(value):
    count = 0
    for birth in value.births.all():
        if birth.status != 'alive':
            count += 1
    return count
