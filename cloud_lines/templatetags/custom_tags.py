from django import template
from django.template import Variable, VariableDoesNotExist

register = template.Library()


@register.simple_tag
def pedigree_column_data(pedigree, data):
    pedigree_context = {'pedigree': pedigree}
    try:
        value = Variable(f"pedigree.{data['db_id']}").resolve(pedigree_context)
    except VariableDoesNotExist:
        value = ""

    # upper/title
    if data['upper']:
        try:
            value = value.upper()
        except AttributeError:
            # must be a NoneType
            pass
    else:
        try:
            value = value.title()
        except AttributeError:
            # must be a decimal
            pass

    # html
    if data['html'] != "":
        value = data['html'].replace('%REPLACEME%', value)
        return value
    else:
        return value

