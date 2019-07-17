from .models import Breeder
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _


class BreederForm(ModelForm):
    class Meta:
        model = Breeder
        fields = '__all__'
        exclude = ('account',)
        help_texts = {
            'prefix': _('The name the breeder goes by e.g. Devon Dogs'),
            'contact_name': _('Point of contact for the breeder'),
            'active': _('Is the breeder currently active?'),
        }