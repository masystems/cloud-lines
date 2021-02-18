from django.urls import path

from . import views

urlpatterns = [
    path('membership', views.Membership.as_view(), name='membership'),
]
