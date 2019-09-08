from django.shortcuts import render
from rest_framework import viewsets
from .serializers import ApiSerializer
from cloud_lines.models import Update
from rest_framework.filters import SearchFilter, OrderingFilter


class UpdateViews(viewsets.ModelViewSet):
    queryset = Update.objects.all()
    serializer_class = ApiSerializer
    filter_backends = [SearchFilter]
    search_fields = ['date', 'body']