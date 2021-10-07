from django.urls import path

from . import views
from pedigree import tabledata

urlpatterns = [
    path('', views.breeders, name='breeders'),
    path('new_breeder/', views.new_breeder_form, name='new_breeder_form'),
    path('<int:breeder_id>/edit_breeder/', views.edit_breeder_form, name='edit_breeder_form'),
    path('<int:breeder_id>/', views.breeder, name='breeder'),
    path('breeder_csv/', views.breeder_csv),
    path('breeder_check', views.breeder_check, name='breeder_check'),
    path('get_breeder_details', views.get_breeder_details, name="get_breeder_details"),
    path('get-ta-breeders/<str:type>', tabledata.get_ta_breeders, name="get_ta_breeders")
]
