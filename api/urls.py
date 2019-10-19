from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('updates', views.UpdateViews)
router.register('pedigrees', views.PedigreeViews, basename='Pedigree')
router.register('authenticate', views.Authenticate)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth', views.CustomAuthToken.as_view())
]