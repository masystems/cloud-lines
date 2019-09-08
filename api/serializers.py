from rest_framework import serializers
from cloud_lines.models import Update


class ApiSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Update
        fields = '__all__'

