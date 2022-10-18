from django.urls import path
from . import tabledata
from . import views

urlpatterns = [
    path('', views.BnHome.as_view(), name='bn_home'),
    path('settings', views.Settings.as_view(), name='bn_settings'),
    path('update_prices', views.update_prices, name='update_prices'),
    path('birth_notification_form', views.birth_notification_form, name='birth_notification_form'),
    path('birth_notification/<int:id>', views.BirthNotificationView.as_view(), name='birth_notification'),
    path('validate_bn_number', views.validate_bn_number, name='validate_bn_number'),
    path('birth_notification_paid/<int:id>', views.birth_notification_paid, name='birth_notification_paid'),
    path('enable_bn/<int:id>', views.enable_bn, name='enable_bn'),
    path('edit_child/<int:id>', views.edit_child, name='edit_child'),
    path('delete_child/<int:id>', views.delete_child, name='delete_child'),
    path('edit_birth_notification/<int:id>', views.edit_birth_notification, name='edit_birth_notification'),
    path('delete_birth_notification/<int:id>', views.delete_birth_notification, name='delete_birth_notification'),
    path('approve_birth_notification/<int:id>', views.approve_birth_notification, name='approve_birth_notification'),
    path('get_births_td', tabledata.get_birth_notifications_td, name='get_births_td'),
    path('validate_bn/<int:id>', views.validate_bn, name='validate_bn'),

]
