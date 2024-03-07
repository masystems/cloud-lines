from django.urls import path
from . import tabledata
from . import views
from . import charging

urlpatterns = [
    path('', views.BnHome.as_view(), name='bn_home'),
    path('settings', views.Settings.as_view(), name='bn_settings'),
    path('update_prices', views.update_prices, name='update_prices'),
    path('birth_notification_form', views.birth_notification_form, name='birth_notification_form'),
    path('bn_checkout/<int:id>/<str:bn_cost_id>/<str:bn_child_cost_id>/<int:no_of_child>', views.bn_checkout, name='bn_checkout'),
    path('bn_checkout_session/<int:id>/<str:bn_cost_id>/<str:bn_child_cost_id>/<int:no_of_child>', charging.bn_checkout_session, name="bn_checkout_session"),
    path('birth_notification_paid', charging.birth_notification_paid, name="birth_notification_paid"),
    path('birth_notification/<int:id>', views.BirthNotificationView.as_view(), name='birth_notification'),
    path('validate_bn_number', views.validate_bn_number, name='validate_bn_number'),
    #path('birth_notification_paid/<int:id>', views.birth_notification_paid, name='birth_notification_paid'),
    path('enable_bn/<int:id>', views.enable_bn, name='enable_bn'),
    path('edit_child/<int:id>', views.edit_child, name='edit_child'),
    path('delete_child/<int:id>', views.delete_child, name='delete_child'),
    path('edit_birth_notification/<int:id>', views.edit_birth_notification, name='edit_birth_notification'),
    path('delete_birth_notification/<int:id>', views.delete_birth_notification, name='delete_birth_notification'),
    path('approve_birth_notification/<int:id>', views.approve_birth_notification, name='approve_birth_notification'),
    path('get_births_td', tabledata.get_birth_notifications_td, name='get_births_td'),
    path('validate_bn/<int:id>', views.validate_bn, name='validate_bn'),
    path('bn_charging_switch', views.bn_charging_switch, name='bn_charging_switch'),

    path('register_pedigree/<int:id>/<str:price>', views.register_pedigree, name='register_pedigree'),
    path('rp_checkout/<int:id>/<str:price>/<str:child_id>', views.rp_checkout, name='rp_checkout'),
    path('rp_checkout_session/<int:id>/<str:price>/<str:child_id>', charging.rp_checkout_session, name="rp_checkout_session"),
    path('register_pedigree_success/<str:pedigree_id>/<str:child_id>', views.register_pedigree_success, name='register_pedigree_success'),
]
