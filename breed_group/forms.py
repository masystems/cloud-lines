from .models import BreedGroup
from django.forms import ModelForm

class BreedGroupForm(ModelForm):
    class Meta:
        model = BreedGroup
        fields = '__all__'