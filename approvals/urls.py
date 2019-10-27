from django.urls import path
from . import views

urlpatterns = [
    path('', views.approvals, name='approvals'),
    path('approve/<int:id>', views.approve, name='approve'),
    path('declined/<int:id>', views.declined, name='declined')
]
