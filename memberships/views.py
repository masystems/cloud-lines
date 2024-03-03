from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Membership
from account.views import is_editor,\
    get_main_account,\
    send_mail
from account.models import AttachedBolton

from urllib.parse import urljoin
import requests

@login_required(login_url="/account/login")
def token(request):
    attached_service = get_main_account(request.user)
    membership = Membership.objects.get(account=attached_service)
    return membership.get_or_create_token()


@login_required(login_url="/account/login")
def enable_bn(request, id):
    # return view from stripe on successful payment of enabling the bn bolton
    attached_service = get_main_account(request.user)
    new_bolton = AttachedBolton.objects.get(id=id)
    new_bolton.active = True
    new_bolton.save()
    attached_service.boltons.add(new_bolton)

    # bolton = requests.get(urljoin(settings.BOLTON_API_URL, str(id))).json()

    # send confirmation email
    # body = f"""<p>This email confirms the successful creation of your new Cloud-Lines bolton.

    #                 <ul>
    #                 <li>Bolton: {bolton['name']}</li>
    #                 <li>Monthly Cost: £{bolton['price']}</li>
    #                 </ul>

    #                 <p>Thank you for purchasing this boloton. Please contact us if you need anything - contact@masys.co.uk</p>

    #                 """
    # send_mail(f"New Bolton Added: {bolton['name']}",
    #            request.user.get_full_name(), body,
    #            send_to=request.user.email)

    return redirect('settings')