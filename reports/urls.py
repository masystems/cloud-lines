from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports, name='reports'),
    path('census/<str:type>', views.census, name='census'),
    path('all/<str:type>', views.all, name='all'),
    path('census_results_complete', views.census_results_complete, name='census_results_complete'),

]
