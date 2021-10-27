from django.urls import path

from . import views

urlpatterns = [
    path('membership', views.Membership.as_view(), name='membership'),
    path('change_bolton_state/<int:bolton_id>/<str:state>', views.change_bolton_state, name='change_bolton_state')
]
