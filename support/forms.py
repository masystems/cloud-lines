from .models import Ticket
from django.forms import ModelForm


class SupportForm(ModelForm):
    class Meta:
        model = Ticket
        fields = '__all__'
        exclude = ('status',)