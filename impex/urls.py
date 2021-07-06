from django.urls import path

from . import views

urlpatterns = [
    path('export', views.export, name='export'),
    path('import', views.importx, name='import'),
    path('import_pedigree_data', views.import_pedigree_data, name='import_pedigree_data'),
    path('import_breeder_data', views.import_breeder_data, name='import_breeder_data'),
    path('import_data', views.import_data, name='import_data'),
    path('image_import', views.image_import, name='image_import')
]
