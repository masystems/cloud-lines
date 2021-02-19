from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports, name='reports'),
    path('census/<str:type>', views.census, name='census'),
]
