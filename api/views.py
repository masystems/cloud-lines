from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.authentication import BasicAuthentication, TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ApiLargeTierQueueSerializer, \
    ApiReportQueueSerializer, \
    ApiAttachedServiceSerializer, \
    ApiPedigreeSerializer, \
    ApiPedigreeImageSerializer,\
    ApiBreederSerializer, \
    ApiBreedSerializer, \
    ApiBreedGroupSerializer, \
    ApiFaqSerializer, \
    ApiBoltonSerializer, \
    ApiKinshipSerializer, \
    ApiDataValidationSerializer, \
    ApiServiceSerializer, \
    ApiStudAdvisorSerializer, \
    ApiBirthNotificationSerializer, \
    ApiBnChildSerializer, \
    ApiUpdateSerializer, \
    ApiAuthentication
from cloud_lines.models import LargeTierQueue
from reports.models import ReportQueue
from pedigree.models import Pedigree, PedigreeImage
from breeder.models import Breeder
from breed.models import Breed
from breed_group.models import BreedGroup
from birth_notifications.models import BirthNotification, BnChild
from cloud_lines.models import Service, Faq, Bolton, Update
from account.models import UserDetail, AttachedService
from metrics.models import KinshipQueue, DataValidatorQueue, StudAdvisorQueue
from memberships.models import Membership
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from account.views import get_main_account
from django.db.models import Q
from django.contrib.auth.models import User



@permission_classes((AllowAny, ))
class LargeTierQueueViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    queryset = LargeTierQueue.objects.all()
    serializer_class = ApiLargeTierQueueSerializer
    filter_backends = [SearchFilter]
    search_fields = '__all__'


@permission_classes((AllowAny, ))
class ReportQueueViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    queryset = ReportQueue.objects.all()
    serializer_class = ApiReportQueueSerializer
    filter_backends = [SearchFilter]
    search_fields = '__all__'


@permission_classes((AllowAny, ))
class ServicesViews(viewsets.ModelViewSet):
    serializer_class = ApiServiceSerializer
    queryset = Service.objects.all()
    filter_backends = [SearchFilter]


class AttachedServiceViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
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



@api_view(['POST',])
@permission_classes((AllowAny, ))
def membership_add_edit_user(request):
    if request.method == 'POST':
        try:
            membership = Membership.objects.get(token=request.data['token'])
        except Membership.DoesNotExist:
            raise PermissionDenied()

        # create user
        user, created = User.objects.get_or_create(email=request.data['email'])
        user.username = request.data['username']
        user.first_name = request.data['first_name']
        user.last_name = request.data['last_name']
        user.save()

        # create user detail
        if created:
            user_detail = UserDetail.objects.create(user=user)
        else:
            user_detail = UserDetail.objects.get(user=user)
        user_detail.phone = request.data['phone']
        user_detail.current_service = membership.account
        user_detail.save()

        # add user to attached service
        if request.data['permission_level'] == 'read_only_users':
            membership.account.read_only_users.add(user)
        elif request.data['permission_level'] == 'contributors':
            membership.account.contributors.add(user)
        elif request.data['permission_level'] == 'admin_users':
            membership.account.admin_users.add(user)
        else:
            return Response({
                'error': True,
                'detail': 'Incorrect permission or no permission level not given'
            })

        return Response({
            'error': False,
            'detail': f'User created: {user.email}'
        })


class PedigreeViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    serializer_class = ApiPedigreeSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = '__all__'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        current_owner = self.request.GET.get('current_owner')
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        account_id = self.request.GET.get('account')
        breeder_breeding_prefix = self.request.GET.get('breeder_breeding_prefix')
        current_owner_breeding_prefix = self.request.GET.get('current_owner_breeding_prefix')

        if account_id:
            try:
                main_account = AttachedService.objects.get(id=account_id)
            except AttachedService.DoesNotExist:
                return Pedigree.objects.none()

            if not (self.request.user.is_superuser or 
                    self.request.user == main_account.user.user or 
                    self.request.user in main_account.admin_users.all()):
                return HttpResponseForbidden("You don't have permission to access these resources.")

        else:
            main_account = get_main_account(self.request.user)

        queryset = Pedigree.objects.filter(account=main_account)

        if from_date and to_date:
            queryset = queryset.filter(date_of_registration__range=[from_date, to_date])

        if current_owner is not None:
            queryset = queryset.filter(current_owner=current_owner)
        
        if breeder_breeding_prefix is not None:
            queryset = queryset.filter(breeder_breeding_prefix=breeder_breeding_prefix)

        if current_owner_breeding_prefix is not None:
            queryset = queryset.filter(current_owner_breeding_prefix=current_owner_breeding_prefix)

        queryset = queryset.filter(status='alive')

        return queryset



class PedigreeImageViews(viewsets.ModelViewSet):
    serializer_class = ApiPedigreeImageSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return PedigreeImage.objects.filter(account=main_account)


class BreederViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    serializer_class = ApiBreederSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = '__all__'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.GET.get('email'):
            return Breeder.objects.filter(user__email=self.request.GET.get('email'))
        else:
            user = self.request.user
            main_account = get_main_account(user)
            return Breeder.objects.filter(account=main_account)


class BreedViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
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


@permission_classes((AllowAny, ))
class FaqViews(viewsets.ModelViewSet):
    serializer_class = ApiFaqSerializer
    queryset = Faq.objects.all()
    filter_backends = [SearchFilter]


@permission_classes((AllowAny, ))
class BoltonViews(viewsets.ModelViewSet):
    serializer_class = ApiBoltonSerializer
    queryset = Bolton.objects.all()
    filter_backends = [SearchFilter]

@permission_classes((AllowAny, ))
class UpdateViews(viewsets.ModelViewSet):
    serializer_class = ApiUpdateSerializer
    queryset = Update.objects.all().order_by('-date')[:3]
    filter_backends = [SearchFilter]

# class Authenticate(viewsets.ModelViewSet):
#     queryset = Update.objects.all()
#     serializer_class = ApiAuthentication


class KinshipViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication)
    serializer_class = ApiKinshipSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return KinshipQueue.objects.all()


class DataValidatorViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication)
    serializer_class = ApiDataValidationSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return DataValidatorQueue.objects.all()


class StudAdvisorViews(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication)
    serializer_class = ApiStudAdvisorSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return StudAdvisorQueue.objects.all()


class BirthNotificationViews(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    serializer_class = ApiBirthNotificationSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return BirthNotification.objects.all()


class BnChildViews(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    authentication_classes = (TokenAuthentication, BasicAuthentication, SessionAuthentication)
    serializer_class = ApiBnChildSerializer
    filter_backends = [SearchFilter]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        main_account = get_main_account(user)
        return BnChild.objects.all()


########## Auth ###########
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