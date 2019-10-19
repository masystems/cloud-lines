from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('updates', views.UpdateViews)
router.register('pedigrees', views.PedigreeViews, basename='Pedigree')
router.register('breeders', views.BreederViews, basename='Breeder')
router.register('breeds', views.BreedViews, basename='Breed')
router.register('breed-groups', views.BreedGroupViews, basename='BreedGroup')
router.register('authenticate', views.Authenticate)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth', views.CustomAuthToken.as_view())
]