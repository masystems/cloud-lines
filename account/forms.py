from .models import SiteDetail
from django.forms import ModelForm

class InstallForm(ModelForm):
    class Meta:
        model = SiteDetail
        fields = '__all__'