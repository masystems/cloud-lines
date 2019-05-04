from django.urls import path

from . import views

urlpatterns = [
    path('', views.breeds, name='breeds'),
    path('new_breed/', views.new_breed_form, name='new_breed_form'),
    path('<int:breed_id>/edit_breed/', views.edit_breed_form, name='edit_breed_form'),
    path('<int:breed_id>/', views.view_breed, name='view_breed'),
]
