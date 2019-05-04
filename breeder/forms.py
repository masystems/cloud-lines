from .models import Breeder
from django.forms import ModelForm

class BreederForm(ModelForm):
    class Meta:
        model = Breeder
        fields = '__all__'