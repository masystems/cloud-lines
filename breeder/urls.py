from django.urls import path

from . import views

urlpatterns = [
    path('', views.breeders, name='breeders'),
    path('new_breeder/', views.new_breeder_form, name='new_breeder_form'),
    path('<int:breeder_id>/edit_breeder/', views.edit_breeder_form, name='edit_breeder_form'),
    path('<int:breeder_id>/', views.breeder, name='breeder'),
    path('breeder_csv/', views.breeder_csv),
    path('breeder_check', views.breeder_check, name='breeder_check')
]
