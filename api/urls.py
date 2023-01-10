from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('large-tier-queue', views.LargeTierQueueViews)
router.register('report-queue', views.ReportQueueViews)
router.register('pedigrees', views.PedigreeViews, basename='Pedigree')
router.register('pedigree-images', views.PedigreeImageViews, basename='PedigreeImage')
router.register('breeders', views.BreederViews, basename='Breeder')
router.register('breeds', views.BreedViews, basename='Breed')
router.register('breed-groups', views.BreedGroupViews, basename='BreedGroup')
router.register('services', views.ServicesViews, basename='services')
router.register('faq', views.FaqViews, basename='faq')
router.register('bolton', views.BoltonViews, basename='bolton')
router.register('kinship', views.KinshipViews, basename='kinship')
router.register('data_validation', views.DataValidatorViews, basename='data_validation')
router.register('stud_advisor', views.StudAdvisorViews, basename='stud_advisor')
router.register('attached-service', views.AttachedServiceViews, basename='AttachedService')
router.register('user', views.UserViews, basename='User')
router.register('user-detail', views.UserDetailViews, basename='UserDetail')
#router.register('authenticate', views.Authenticate)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth', views.CustomAuthToken.as_view())
]