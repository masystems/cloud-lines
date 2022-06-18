from django.urls import path

from . import views

urlpatterns = [
    path('', views.BnHome.as_view(), name='bn_home'),
    path('birth_notification_form', views.birth_notification_form, name='birth_notification_form'),
    path('birth_notification/<int:id>', views.BirthNotificationView.as_view(), name='birth_notification'),
    path('edit_child/<int:id>', views.edit_child, name='edit_child'),
    path('delete_child/<int:id>', views.delete_child, name='delete_child'),
    path('edit_birth_notification/<int:id>', views.edit_birth_notification, name='edit_birth_notification'),
    path('delete_birth_notification/<int:id>', views.delete_birth_notification, name='delete_birth_notification'),
    path('toggle_birth_notification/<int:id>', views.toggle_birth_notification, name='toggle_birth_notification'),

]
