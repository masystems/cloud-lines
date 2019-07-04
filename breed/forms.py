from .models import Breed
from django import forms
from django.utils.translation import gettext_lazy as _


class BreedForm(forms.ModelForm):
    class Meta:
        model = Breed
        fields = '__all__'
        exclude = ('account',)
        help_texts = {
            'breed_name': _('e.g. Greyhound, Siamese, Shetland, etc'),
            'image': _('A great picture to depict the breed.'),
            'description': _('What are the common attributes about this breed?')
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 15, 'maxlength': '2000',}),
        }
