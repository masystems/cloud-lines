from django.urls import path
from . import tabledata
from . import views

urlpatterns = [
    path('search', views.search, name='pedigree_search'),
    path('<int:pedigree_id>', views.ShowPedigree.as_view(), name='pedigree'),
    path('new_pedigree/', views.new_pedigree_form, name='new_pedigree_form'),
    path('<int:id>/edit_pedigree/', views.edit_pedigree_form, name='edit_pedigree_form'),
    path('<int:id>/image_upload_pedigree/', views.image_upload, name='image_upload'),
    path('<int:pedigree_id>/add_existing', views.add_existing, name='add_existing'),
    path('<int:pedigree_id>/add_existing_parent', views.add_existing_parent, name='add_existing_parent'),
    path('<int:pedigree_id>/certificate/<str:type>', views.GeneratePDF.as_view(), name='cert'),
    path('get-pedigrees', tabledata.get_pedigrees, name="get_pedigrees"),
    path('get_pedigree_details', views.get_pedigree_details, name="get_pedigree_details"),
    path('get_breeder_details', views.get_breeder_details, name="get_breeder_details"),
    path('get-ta-pedigrees/<str:sex>/<str:state>/<str:avoid>', tabledata.get_ta_pedigrees, name="get_ta_pedigrees"),
    path('get-ta-breeders/<str:type>', tabledata.get_ta_breeders, name="get_ta_breeders")
]
