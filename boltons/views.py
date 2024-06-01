from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor, get_main_account, get_stripe_secret_key, get_stripe_public_key
from account.models import AttachedBolton, UserDetail
from urllib.parse import urljoin
import requests
import stripe


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


@login_required(login_url="/account/login")
def change_bolton_state(request, bolton_id, req_state):
    # security checks
    # ensure user is superadmin or owner
    attached_service = get_main_account(request.user)
    if request.user.id is not attached_service.user.user.id:
        return redirect('settings', f"You don't have permission to activate boltons. Error:{request.user.id}-{attached_service.user.user.id}")
    # ensure account is != small tier

    # get bolton from API
    try:
        bolton = requests.get(urljoin(settings.BOLTON_API_URL, str(bolton_id))).json()
    except:
        return redirect('settings', "Unable to enable boltons at this time")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # if activation request
    if req_state == "enable":
        # ensure bolton is not already active
        if attached_service.boltons.filter(bolton=bolton['id'], active=True).exists():
            return redirect('settings', "Bolton already exists!")
        else:
            #  redirect to bolton charding
            if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
                price = bolton['test_stripe_price_id']
            else:
                price = bolton['stripe_price_id']
            return redirect('bolton_checkout', bolton['id'], price)

    # if deactivation request
    elif req_state == "disable":
        attached_bolton = AttachedBolton.objects.get(bolton=bolton['id'], active=True)
        # ensure bolton is deactivated
        attached_bolton.active = False
        attached_bolton.save()

        # cancel subscription in strip
        stripe.Subscription.delete(attached_bolton.stripe_sub_id)
    return redirect('settings', "Unknown error, please contact support")


@login_required(login_url="/account/login")
def bolton_checkout(request, bolton_id, price):
    # id = pedigree DB ID
    return render(request, 'bolton_checkout.html', {'price': price,
                                                    'bolton_id': bolton_id,
                                                    'stripe_pk': get_stripe_public_key(request)})


@csrf_exempt
def bolton_charging_session(request, bolton_id, price):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    user_detail = UserDetail.objects.get(user=request.user)

    # get customer
    customer = stripe.Customer.retrieve(user_detail.stripe_id)

    new_bolton = AttachedBolton.objects.create(bolton=bolton_id, active=False)

    bolton = requests.get(urljoin(settings.BOLTON_API_URL, str(bolton_id))).json()

    return_urls = {1: 'birth_notification',
                   2: 'memberships'}

    # create session
    session = stripe.checkout.Session.create(
        ui_mode='embedded',
        payment_method_types=['card'],
        line_items=[
            {
                "price": price,
                "quantity": 1
            }
        ],
        mode='subscription',
        customer=attached_service.user.stripe_id,
        return_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/{return_urls[bolton['id']]}/enable_bn/{new_bolton.id}",
    )
    new_bolton.stripe_payment_token=session['id']
    new_bolton.save()

    return JsonResponse({'clientSecret': session.client_secret})