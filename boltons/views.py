from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor, get_main_account
import requests

# Create your views here.
class MembershipBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)

        return context


class Membership(MembershipBase):
    template_name = 'membership/membership.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def change_bolton_state(request, bolton_id, state):
    print(bolton_id)
    print(state)
    # security checks
    # ensure user is superadmin or owner
    # ensure account is != small tier

    # get bolton from API
    boltons = requests.get(settings.BOLTON_API_URL).json()
    from pprint import pprint
    pprint(boltons)
    #if state == 'enable' and :

    # if activation request
    # ensure bolton is not already active
    # check valid payment option exists
    # set up subscription in stripe
    # enable bolt on

    # if deactivation request
    # ensure bolton is deactivated
    # cancel subscription in strip
    # disable bolton
    return redirect('settings')