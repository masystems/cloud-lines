from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt

from .models import BirthNotification
from account.models import StripeAccount, UserDetail
from account.views import is_editor,\
    get_main_account,\
    has_permission,\
    redirect_2_login,\
    get_stripe_secret_key

import stripe


def bn_charging_session(request, pedigree, child, price):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    stripe_account = StripeAccount.objects.get(account=attached_service)
    user_detail = UserDetail.objects.get(user=request.user)

    # get or create customer
    if not user_detail.bn_stripe_id:
        customer = stripe.Customer.create(
            email=user_detail.user.email,
            stripe_account=stripe_account.stripe_acct_id
        )
        user_detail.bn_stripe_id = customer['id']
    else:
        customer = stripe.Customer.retrieve(user_detail.bn_stripe_id,
                                            stripe_account=stripe_account.stripe_acct_id)

    # create session
    session = stripe.checkout.Session.create(
        ui_mode='embedded',
        payment_method_types=['card'],
        line_items=[
            {
                "price": price,
                "quantity": 1,
            },
        ],
        mode='payment',
        customer=customer.id,
        return_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/birth_notification/register_pedigree_success/{child.id}/{pedigree.id}",
        stripe_account=stripe_account.stripe_acct_id,
    )
    pedigree.stripe_payment_token = session['id']
    pedigree.save()
    return session.url


@csrf_exempt
@login_required(login_url="/account/login")
def bn_checkout_session(request, id, bn_cost_id, bn_child_cost_id, no_of_child):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    stripe_account = StripeAccount.objects.get(account=attached_service)
    user_detail = UserDetail.objects.get(user=request.user)
    bn = BirthNotification.objects.get(id=id)
    # get or create customer
    if not user_detail.bn_stripe_id:
        customer = stripe.Customer.create(
            email=user_detail.user.email,
            stripe_account=stripe_account.stripe_acct_id
        )
        user_detail.bn_stripe_id = customer['id']
    else:
        customer = stripe.Customer.retrieve(user_detail.bn_stripe_id,
                                            stripe_account=stripe_account.stripe_acct_id)

    # create session
    session = stripe.checkout.Session.create(
        ui_mode='embedded',
        payment_method_types=['card'],
        line_items=[
            {
                "price": bn_cost_id,
                "quantity": 1,
            },
            {
                "price": bn_child_cost_id,
                "quantity": no_of_child,
            },
        ],
        mode='payment',
        customer=customer.id,
        return_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/birth_notification/birth_notification_paid" + f"?id={bn.id}&" + "session_id={CHECKOUT_SESSION_ID}",
        stripe_account=stripe_account.stripe_acct_id,
    )

    return JsonResponse({'clientSecret': session.client_secret})


def birth_notification_paid(request):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    stripe_account = StripeAccount.objects.get(account=attached_service)
    session = stripe.checkout.Session.retrieve(request.GET.get('session_id', ''),
                                               stripe_account=stripe_account.stripe_acct_id)
    if session.payment_status == 'paid':
        BirthNotification.objects.filter(id=request.GET.get('id', '')).update(paid=True, 
                                                                     stripe_payment_token=request.GET.get('session_id', ''))
    return redirect('birth_notification', request.GET.get('id', ''))