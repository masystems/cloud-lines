from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Pedigree
from account.currencies import get_currencies
from account.models import StripeAccount, UserDetail
from account.views import is_editor,\
    get_main_account,\
    has_permission,\
    redirect_2_login,\
    get_stripe_secret_key,\
    get_stripe_connected_account_links

import json
import stripe

class PedigreePaymentSettings(LoginRequiredMixin, TemplateView):
    template_name = 'pedigree_payment_settings.html'

    def get_context_data(self, **kwargs):
        # check if user has permission
        if self.request.method == 'GET':
            if not has_permission(self.request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': False}):
                return redirect_2_login(request)
        elif self.request.method == 'POST':
            if not has_permission(self.request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
                raise PermissionDenied()
        else:
            raise PermissionDenied()

        context = super().get_context_data(**kwargs)
        context['attached_service'] = get_main_account(self.request.user)
        context['prices'] = get_pedigree_prices(self.request, context['attached_service'])
        context['currencies'] = get_currencies()
        return context


def get_pedigree_prices(request, attached_service):
    stripe.api_key = get_stripe_secret_key(request)
    stripe_account = StripeAccount.objects.get(account=attached_service)
    # ensure Pedigree product exists
    products = stripe.Product.list(limit=100,
                                   stripe_account=stripe_account.stripe_acct_id)
    pedigree_product_id = None
    for product in products:
        if product['name'] == 'Pedigree':
            pedigree_product_id = product.id

    if not pedigree_product_id:
        # create the product if it does not exist
        new_pedigree_product = stripe.Product.create(name="Pedigree",
                                                     stripe_account=stripe_account.stripe_acct_id)
        pedigree_product_id = new_pedigree_product.id

    # get prices for pedigree product
    return stripe.Price.list(limit=100,
                             product=pedigree_product_id,
                             active=True,
                             stripe_account=stripe_account.stripe_acct_id)


@login_required(login_url="/account/login")
def pedigree_price_edit(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    stripe_account = StripeAccount.objects.get(account=attached_service)
    # get predigree product
    products = stripe.Product.list(limit=100,
                                   stripe_account=stripe_account.stripe_acct_id)
    pedigree_product = None
    for product in products:
        if product['name'] == 'Pedigree':
            pedigree_product = product.id

    price = request.POST

    if price['formType'] == 'new':
        try:
            price = stripe.Price.create(
                        product=pedigree_product,
                        unit_amount=int(float(price['fieldPrice'].replace('£','')) * 100),
                        nickname=price['fieldType'],
                        currency=price['currency'],
                        stripe_account=stripe_account.stripe_acct_id
                    )
        except ValueError:
            print('value error!')
            return HttpResponse(json.dumps({'result': 'fail', 'error': 'Price must be a numerical value.'}))
    # Delete price
    elif price['formType'] == 'delete':
        price = stripe.Price.modify(
                    price['id'],
                    active=False,
                    stripe_account=stripe_account.stripe_acct_id
                )

    return HttpResponse(json.dumps({'result': 'success'}))


def pedigree_charging_session(request, pedigree, price):
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
        success_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/pedigree/pedigree_paid/{pedigree.id}",
        cancel_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/pedigree/search",
        stripe_account=stripe_account.stripe_acct_id,
    )
    pedigree.stripe_payment_token = session['id']
    pedigree.save()
    return session.url


def pedigree_paid(request, id):
    Pedigree.objects.filter(id=id).update(paid=True)
    return redirect('pedigree', id)


def decline_pedigree(request, reg_no):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    if not attached_service.pedigree_charging:
        return
    stripe_account = StripeAccount.objects.get(account=attached_service)
    pedigree = Pedigree.objects.get(reg_no=reg_no)

    # submit refund
    session = stripe.checkout.Session.retrieve(
        pedigree.stripe_payment_token,
        stripe_account=stripe_account.stripe_acct_id
    )

    if session['payment_status'] == 'paid':
        payment_intent = stripe.PaymentIntent.retrieve(
            session.payment_intent,
            stripe_account=stripe_account.stripe_acct_id
        )

        # create refund
        stripe.Refund.create(
            charge=payment_intent['charges']['data'][0]['id'],
            stripe_account=stripe_account.stripe_acct_id
        )


def get_pedigree_payment_session(request, pedigree):
    stripe.api_key = get_stripe_secret_key(request)
    attached_service = get_main_account(request.user)
    if not attached_service.pedigree_charging:
        return
    stripe_account = StripeAccount.objects.get(account=attached_service)
    session = stripe.checkout.Session.retrieve(
        pedigree.stripe_payment_token,
        stripe_account=stripe_account.stripe_acct_id
    )
    return session