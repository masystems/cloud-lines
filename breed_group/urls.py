from django.urls import path

from . import views

urlpatterns = [
    path('', views.breed_groups, name='breed_groups'),
    path('new_breed_group/', views.new_breed_group_form, name='new_breed_group_form'),
    path('<int:breed_group_id>/edit_breed_group/', views.edit_breed_group_form, name='edit_breed_group_form'),
]
