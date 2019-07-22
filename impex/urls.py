from django.urls import path

from . import views

urlpatterns = [
    path('export', views.export, name='export'),
    path('import', views.importx, name='import'),
]
