from django.urls import path

from . import views

urlpatterns = [
    path('', views.BnHome.as_view(), name='bn_home'),
    path('birth_notification_form', views.birth_notification_form, name='birth_notification_form'),
]
