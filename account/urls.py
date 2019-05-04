from django.urls import path
from . import views

urlpatterns = [
    # path('signup', views.signup, name='signup'),
    path('login', views.site_login, name='login'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile, name='profile'),
    path('install', views.install, name='install'),
]