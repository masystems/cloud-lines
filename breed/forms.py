from .models import Breed
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _


class BreedForm(ModelForm):
    class Meta:
        model = Breed
        fields = '__all__'
        exclude = ('account',)
        help_texts = {
            'breed_name': _('Some useful help text.'),
        }
