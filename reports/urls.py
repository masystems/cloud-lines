from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports, name='reports'),
    path('census/<str:type>', views.census, name='census'),
    path('all/<str:type>', views.all, name='all'),
    path('all_animals_by_boo', views.all_animals_by_boo, name='animals_by_breeder'),
    path('census_results_complete', views.census_results_complete, name='census_results_complete'),
    path('fangr', views.fangr, name='fangr')
]
