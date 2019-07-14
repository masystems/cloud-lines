from django.contrib import admin
from django.urls import path, include

from cloud_lines import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('extras/', views.extras, name='extras'),
    path('faqs/', views.faqs, name='faqs'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('order/', views.order, name='order'),
    path('know_more/', views.know_more, name='know_more'),
    path('order/service', views.order_service, name='order_service'),
    path('order/billing', views.order_billing, name='order_billing'),
    path('order/subscribe', views.order_subscribe, name='order_subscribe'),
    path('pedigree/', include('pedigree.urls')),
    path('breeders/', include('breeder.urls')),
    path('breeds/', include('breed.urls')),
    path('breed_groups/', include('breed_group.urls')),
    path('account/', include('account.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('support/', include('support.urls')),
    path('dashboard', views.dashboard, name='dashboard'),
    path('primary_account/<str:service>', views.activate_primary_account, name='primary_account'),
]
