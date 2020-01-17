from rest_framework import serializers
from cloud_lines.models import Update
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed.models import Breed
from breed_group.models import BreedGroup
from cloud_lines.models import Service
from account.models import AttachedService
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