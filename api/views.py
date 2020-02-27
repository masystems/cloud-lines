from django.shortcuts import render
from rest_framework import viewsets
from .serializers import ApiUpdatesSerializer, \
    ApiAttachedServiceSerializer, \
    ApiPedigreeSerializer, \
    ApiPedigreeImageSerializer,\
    ApiBreederSerializer, \
    ApiBreedSerializer, \
    ApiBreedGroupSerializer, \
    ApiServiceSerializer, \
    ApiAuthentication
from cloud_lines.models import Update
from pedigree.models import Pedigree, PedigreeImage
from breeder.models import Breeder
from breed.models import Breed
from breed_group.models import BreedGroup
from cloud_lines.models import Service
from account.models import UserDetail, AttachedService
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import authentication_classes, permission_classes
from account.views import get_main_account
from django.db.models import Q


@permission_classes((AllowAny, ))
class UpdateViews(viewsets.ModelViewSet):
    queryset = Update.objects.all()
    serializer_class = ApiUpdatesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['date', 'body']


@permission_classes((AllowAny, ))
class ServicesViews(viewsets.ModelViewSet):
    serializer_class = ApiServiceSerializer
    queryset = Service.objects.all()
    filter_backends = [SearchFilter]


class AttachedServiceViews(viewsets.ModelViewSet):
    serializer_class = ApiAttachedServiceSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_detail = UserDetail.objects.get(user=user)
        return AttachedService.objects.filter(Q(admin_users=user, active=True) |
                                              Q(contributors=user, active=True) |
                                              Q(read_only_users=user, active=True) |
                                              Q(user=user_detail, active=True)).distinct().distinct()


class PedigreeViews(viewsets.ModelViewSet):
    serializer_class = ApiPedigreeSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return Pedigree.objects.filter(account=main_account)


class PedigreeImageViews(viewsets.ModelViewSet):
    serializer_class = ApiPedigreeImageSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return PedigreeImage.objects.filter(account=main_account)


class BreederViews(viewsets.ModelViewSet):
    serializer_class = ApiBreederSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return Breeder.objects.filter(account=main_account)


class BreedViews(viewsets.ModelViewSet):
    serializer_class = ApiBreedSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return Breed.objects.filter(account=main_account)


class BreedGroupViews(viewsets.ModelViewSet):
    serializer_class = ApiBreedGroupSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return BreedGroup.objects.filter(account=main_account)


class Authenticate(viewsets.ModelViewSet):
    queryset = Update.objects.all()
    serializer_class = ApiAuthentication


from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })