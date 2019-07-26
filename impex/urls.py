from django.urls import path

from . import views

urlpatterns = [
    path('export', views.export, name='export'),
    path('import', views.importx, name='import'),
    path('import_data', views.import_data, name='import_data')
]
