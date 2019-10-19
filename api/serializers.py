from rest_framework import serializers
from cloud_lines.models import Update
from pedigree.models import Pedigree
from django.contrib.auth.models import User


class ApiUpdatesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Update
        fields = '__all__'


class ApiPedigreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedigree
        fields = '__all__'


class ApiAuthentication(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
