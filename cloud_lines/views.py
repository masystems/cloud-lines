from django.shortcuts import render
from .models import Service
# Create your views here.

def home(request):
    return render(request, 'home.html', {'services': Service.objects.all()})