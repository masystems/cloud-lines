from django.urls import path
from . import views

urlpatterns = [
    path('', views.metrics, name='metrics'),
    path('kinship', views.kinship, name='kinship'),
    path('run_mean_kinship', views.run_mean_kinship, name='run_mean_kinship'),
    path('run_coi', views.run_coi, name='run_coi'),
    path('stud_advisor', views.stud_advisor, name='stud_advisor'),
    path('stud_advisor_mother_details', views.stud_advisor_mother_details, name='stud_advisor_mother_details'),

]
