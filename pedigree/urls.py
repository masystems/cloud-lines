from django.urls import path
from . import tabledata
from . import views

urlpatterns = [
    path('search', views.search, name='pedigree_search'),
    path('<int:pedigree_id>', views.ShowPedigree.as_view(), name='pedigree'),
    path('results/', views.search_results, name='results'),
    path('new_pedigree/', views.new_pedigree_form, name='new_pedigree_form'),
    path('<int:id>/edit_pedigree/', views.edit_pedigree_form, name='edit_pedigree_form'),
    path('<int:id>/image_upload_pedigree/', views.image_upload, name='image_upload'),
    path('<int:pedigree_id>/add_existing', views.add_existing, name='add_existing'),
    path('<int:pedigree_id>/add_existing_parent', views.add_existing_parent, name='add_existing_parent'),
    path('<int:pedigree_id>/certificate', views.GeneratePDF.as_view(), name='cert'),
    path('get-pedigrees>', tabledata.get_pedigrees, name="get_pedigrees"),
    path('get_pedigree_details', views.get_pedigree_details, name="get_pedigree_details")
]
