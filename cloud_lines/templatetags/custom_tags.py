from django import template
from django.template import Variable, VariableDoesNotExist

register = template.Library()


@register.simple_tag
def pedigree_column_data(pedigree, db_id, html=""):
    pedigree_context = {'pedigree': pedigree}
    try:
        value = Variable(f"pedigree.{db_id}").resolve(pedigree_context)
    except VariableDoesNotExist:
        value = None

    if html != "":
        try:
            value = html.replace('%REPLACEME%', value.title())
            return value
        except AttributeError:
            return value

    else:
        try:
            return value.title()
        except AttributeError:
            return value

