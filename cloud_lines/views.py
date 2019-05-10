from django.shortcuts import render
from .models import Service
# Create your views here.

def home(request):
    return render(request, 'home.html', {'services': Service.objects.all()})

def about(request):
    return render(request, 'about.html', {'services': Service.objects.all()})