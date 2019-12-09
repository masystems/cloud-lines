from django.urls import path
from . import views

urlpatterns = [
    path('', views.metrics, name='metrics'),
    path('kinship', views.kinship, name='kinship'),
    path('mean_kinship', views.mean_kinship, name='mean_kinship'),
    path('run_coi', views.run_coi, name='run_coi'),
]
