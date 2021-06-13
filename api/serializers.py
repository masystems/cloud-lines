from rest_framework import serializers
from cloud_lines.models import Update
from pedigree.models import Pedigree, PedigreeImage
from breeder.models import Breeder
from breed.models import Breed
from breed_group.models import BreedGroup
from cloud_lines.models import Service, Faq
from account.models import AttachedService
from metrics.models import KinshipQueue, DataValidatorQueue
from django.contrib.auth.models import User


class ApiUpdatesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Update
        fields = '__all__'


class ApiAttachedServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttachedService
        fields = '__all__'


class ApiPedigreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedigree
        fields = '__all__'


class ApiPedigreeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedigreeImage
        fields = '__all__'


class ApiBreederSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breeder
        fields = '__all__'


class ApiBreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = '__all__'


class ApiBreedGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreedGroup
        fields = '__all__'


class ApiFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = '__all__'


class ApiAuthentication(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class ApiServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('service_name',
                  'price_per_month',
                  'admin_users',
                  'contrib_users',
                  'read_only_users',
                  'number_of_animals',
                  'multi_breed',
                  'active')


class ApiKinshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = KinshipQueue
        fields = '__all__'


class ApiDataValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataValidatorQueue
        fields = '__all__'