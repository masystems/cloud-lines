from django.urls import path

from . import views

urlpatterns = [
    path('membership', views.Membership.as_view(), name='membership'),
    path('change_bolton_state/<int:bolton_id>/<str:req_state>', views.change_bolton_state, name='change_bolton_state'),
    path('bolton_checkout/<int:bolton_id>/<str:price>', views.bolton_checkout, name="bolton_checkout"),
    path('bolton_checkout_session/<int:bolton_id>/<str:price>', views.bolton_charging_session, name="bolton_charging_session"),
]
