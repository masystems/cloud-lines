from django.urls import path
from . import views

urlpatterns = [
    # path('signup', views.signup, name='signup'),
    path('login', views.site_login, name='cl_login'),
    path('logout', views.logout, name='cl_logout'),
    path('profile', views.profile, name='profile'),
    path('settings', views.settings, name='settings'),
    path('setup', views.setup, name='setup'),
    path('register', views.register, name='register'),
    path('username_check', views.username_check, name='username_check'),
    path('email_check', views.email_check, name='email_check'),
    path('user_edit', views.user_edit, name='user_edit'),
    path('custom_field_edit', views.custom_field_edit, name='custom_field_edit'),
    path('update_card', views.update_card, name='update_card'),
    path('update_user', views.update_user, name='update_user')
]