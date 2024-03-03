from django.urls import path
from . import views

urlpatterns = [
    path('token', views.token, name='membership_token'),
    path('enable_bn/<int:id>', views.enable_bn, name='enable_bn'),
]