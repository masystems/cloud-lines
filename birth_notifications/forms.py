from .models import BirthNotification, BnChild
from django import forms
from django.utils.translation import gettext_lazy as _


class BirthNotificationForm(forms.ModelForm):
    class Meta:
        model = BirthNotification
        fields = '__all__'
        exclude = ('account', 'user', 'attached_bolton', 'births', 'complete')
        help_texts = {
            # 'breed_name': _('e.g. Greyhound, Siamese, Shetland, etc'),
            # 'image': _('A great picture to depict the breed.'),
            # 'breed_description': _('What are the common attributes about this breed?')
        }
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'cols': 15, 'maxlength': 2000,}),
        }


class BirthForm(forms.ModelForm):
    class Meta:
        model = BnChild
        fields = '__all__'
        exclude = ('approved',)
        help_texts = {
            # 'breed_name': _('e.g. Greyhound, Siamese, Shetland, etc'),
            # 'image': _('A great picture to depict the breed.'),
            # 'breed_description': _('What are the common attributes about this breed?')
        }
        widgets = {
            # 'comments': forms.Textarea(attrs={'rows': 4, 'cols': 15, 'maxlength': 2000, }),
        }
