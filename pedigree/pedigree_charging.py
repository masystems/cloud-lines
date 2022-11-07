from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

from account.models import StripeAccount
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

        stripe.api_key = get_stripe_secret_key(self.request)
        context['attached_service'] = get_main_account(self.request.user)
        context['stripe_account'] = StripeAccount.objects.get(account=context['attached_service'])

        # ensure Pedigree product exists
        products = stripe.Product.list(limit=100,
                                       stripe_account=context['stripe_account'].stripe_acct_id)
        pedigree_product_id = None
        for product in products:
            if product['name'] == 'Pedigree':
                pedigree_product_id = product.id

        if not pedigree_product_id:
            # create the product if it does not exists
            new_pedigree_product = stripe.Product.create(name="Pedigree",
                                                         stripe_account=context['stripe_account'].stripe_acct_id)
            pedigree_product_id = new_pedigree_product.id

        # get prices for pedigree product
        context['prices'] = stripe.Price.list(limit=100,
                                              product=pedigree_product_id,
                                              active=True,
                                              stripe_account=context['stripe_account'].stripe_acct_id)

        return context


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
        price = stripe.Price.create(
                    product=pedigree_product,
                    unit_amount=int(float(price['fieldPrice'].replace('£','')) * 100),
                    nickname=price['fieldType'],
                    currency="gbp",
                    stripe_account=stripe_account.stripe_acct_id
                )
    # Delete price
    elif price['formType'] == 'delete':
        price = stripe.Price.modify(
                    price['id'],
                    active=False,
                    stripe_account=stripe_account.stripe_acct_id
                )

    return HttpResponse(json.dumps({'result': 'success'}))