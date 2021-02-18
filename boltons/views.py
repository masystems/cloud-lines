from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from account.views import is_editor, get_main_account

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
