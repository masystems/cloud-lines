from django.urls import path

from . import views

urlpatterns = [
    path('', views.BnHome.as_view(), name='bn_home'),
    path('birth_notification_form', views.birth_notification_form, name='birth_notification_form'),
    path('birth_notification/<int:id>', views.BirthNotificationView.as_view(), name='birth_notification'),
    path('child_approval/<int:id>/<str:approved>', views.child_approval, name='child_approval')
]
