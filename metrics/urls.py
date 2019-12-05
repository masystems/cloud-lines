from django.urls import path
from . import views

urlpatterns = [
    path('', views.metrics, name='metrics'),
    path('coi', views.coi, name='coi'),
    path('mean_kinship', views.mean_kinship, name='mean_kinship'),
]
