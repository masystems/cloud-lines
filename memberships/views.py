from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Membership
from account.views import is_editor,\
    get_main_account,\
    has_permission,\
    redirect_2_login,\
    get_stripe_secret_key,\
    get_stripe_connected_account_links


@login_required(login_url="/account/login")
def token(request):
    attached_service = get_main_account(request.user)
    membership = Membership.objects.get(account=attached_service)
    return membership.get_or_create_token()