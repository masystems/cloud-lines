from django.urls import path
from . import views

urlpatterns = [
    path('', views.metrics, name='metrics'),
    path('coi', views.coi, name='coi'),
]
