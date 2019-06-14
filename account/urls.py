from django.urls import path
from . import views

urlpatterns = [
    # path('signup', views.signup, name='signup'),
    path('login', views.site_login, name='login'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile, name='profile'),
    path('install', views.install, name='install'),
    path('register', views.register, name='register'),
    path('username_check', views.username_check, name='username_check'),
    path('email_check', views.email_check, name='email_check'),
    path('user_edit', views.user_edit, name='user_edit')
]