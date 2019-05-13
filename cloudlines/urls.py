from django.contrib import admin
from django.urls import path, include

from cloud_lines import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about', views.about, name='about'),
    path('extras', views.extras, name='extras'),
    path('faqs', views.faqs, name='faqs'),
    path('contact', views.contact, name='contact'),
    path('result/<str:result>', views.result, name='result'),
    path('pedigree/', include('pedigree.urls')),
    path('breeders/', include('breeder.urls')),
    path('breeds/', include('breed.urls')),
    path('breed_groups/', include('breed_group.urls')),
    path('account/', include('account.urls')),
    path('support/', include('support.urls'))
]