from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Pedigree
from account.models import StripeAccount, UserDetail
from account.views import is_editor,\
    get_main_account,\
    has_permission,\
    redirect_2_login,\
    get_stripe_secret_key,\
    get_stripe_connected_account_links

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
        payment_method_types=['card'],
        line_items=[
            {
                "price": price,
                "quantity": 1,
            },
        ],
        mode='payment',
        customer=customer.id,
        success_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/birth_notification/register_pedigree_success/{child.id}/{pedigree.id}",
        cancel_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/birth_notification/{child.births.all()[0].id}",
        stripe_account=stripe_account.stripe_acct_id,
    )
    pedigree.stripe_payment_token = session['id']
    pedigree.save()
    return session.url
