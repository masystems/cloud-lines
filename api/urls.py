from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('updates', views.UpdateViews)

urlpatterns = [
    path('', include(router.urls))
]