from django.shortcuts import render
from rest_framework import viewsets
from .serializers import ApiUpdatesSerializer, ApiPedigreeSerializer, ApiAuthentication
from cloud_lines.models import Update
from pedigree.models import Pedigree
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import authentication_classes, permission_classes
from account.views import get_main_account


@permission_classes((AllowAny, ))
class UpdateViews(viewsets.ModelViewSet):
    queryset = Update.objects.all()
    serializer_class = ApiUpdatesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['date', 'body']


class PedigreeViews(viewsets.ModelViewSet):
    serializer_class = ApiPedigreeSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return Pedigree.objects.filter(account=main_account)


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