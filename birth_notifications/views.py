from django.shortcuts import render, redirect, HttpResponse
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from account.models import AttachedBolton
from .models import BirthNotification, BnChild, BnStripeAccount
from .forms import BirthNotificationForm, BirthForm
from pedigree.models import Pedigree
from json import dumps
from urllib.parse import parse_qs
import re
import stripe


# Create your views here.
class BirthNotificationBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)
        context['birth_notifications'] = BirthNotification.objects.filter(account=context['attached_service'])
        context['latest'] = context['birth_notifications'].filter(account=context['attached_service']).order_by('-id')[:10]

        return context


class BnHome(BirthNotificationBase):
    template_name = 'bn_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_living'] = context['birth_notifications'].filter(births__status="alive").count()
        context['total_deceased'] = context['birth_notifications'].filter(births__status="deceased").count()
        context['approvals'] = BirthNotification.objects.filter(account=context['attached_service'], complete=False)

        if self.request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

        if self.request.user == context['attached_service'].user.user:
            try:
                context['bn_stripe_account'] = BnStripeAccount.objects.get(account=context['attached_service'])
            except BnStripeAccount.DoesNotExist:
                context['account_link'] = create_package_on_stripe(self.request)
                context['bn_stripe_account'] = BnStripeAccount.objects.get(account=context['attached_service'])

            context['stripe_package'] = stripe.Account.retrieve(context['bn_stripe_account'].stripe_acct_id)

            if context['bn_stripe_account'].stripe_acct_id:
                try:
                    context['edit_account'] = stripe.Account.create_login_link(context['bn_stripe_account'].stripe_acct_id)
                except stripe.error.InvalidRequestError:
                    # stripe account created but not setup
                    context['stripe_package_setup'] = get_account_link(context['bn_stripe_account'], context['attached_service'])
                if context['stripe_package'].requirements.errors:
                    context['account_link'] = get_account_link(context['bn_stripe_account'], context['attached_service'])
            else:
                # stripe account not setup
                context['stripe_package_setup'] = create_package_on_stripe(self.request)

        return context


class Settings(BirthNotificationBase):
    template_name = 'bn_settings.html'

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
        context['bn_stripe_account'] = BnStripeAccount.objects.get(account=context['attached_service'])
        return context


@login_required(login_url="/account/login")
def update_prices(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
    print(request.POST)
    print(request.POST.get('bncost'))

    attached_service = get_main_account(request.user)

    bn_stripe_account = BnStripeAccount.objects.get(account=attached_service)
    bn_stripe_account.bn_cost = float(request.POST.get('bncost')) * 100
    bn_stripe_account.bn_child_cost = float(request.POST.get('bnccost')) * 100
    bn_stripe_account.save()
    
    return redirect('bn_settings')


class BirthNotificationView(BirthNotificationBase):
    template_name = 'birth_notification.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['bn'] = BirthNotification.objects.get(id=self.kwargs['id'])
        return context


@login_required(login_url="/account/login")
def birth_notification_form(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    attached_service = get_main_account(request.user)

    try:
        bn_stripe_account = BnStripeAccount.objects.get(account=attached_service)
    except BnStripeAccount.DoesNotExist:
        bn_stripe_account = False

    if request.method == 'POST':
        #bn_form = BirthNotificationForm(request.POST or None)
        try:
            bn_form = parse_qs(request.POST['form'])
        except MultiValueDictKeyError:
            bn_form = request.POST

        new_bn = BirthNotification()
        ### mother ###
        try:
            new_bn.mother = Pedigree.objects.get(account=attached_service,
                                                  reg_no=bn_form['motherx'][0])
        except:
            pass

        ### father ###
        try:
            new_bn.father = Pedigree.objects.get(account=attached_service,
                                                  reg_no=bn_form['fatherx'][0])
        except:
            pass

        new_bn.user = request.user
        new_bn.account = attached_service
        # not currently validating against other bn numbers on same instance
        new_bn.bn_number = bn_form['bn_number'][0]
        try:
            new_bn.dob = bn_form['dob'][0]
        except KeyError:
            # no date added
            pass
        try:
            new_bn.comments = bn_form['comments'][0]
        except KeyError:
            # no comment added
            pass

        # needs to be moved to after adding children
        try:
            new_bn.save()
        except IntegrityError:
            result = {'result': 'fail',
                      'feedback': f'BN Number: {bn_form["bn_number"][0]} already in use!'}
            return HttpResponse(dumps(result))

        # births and calc total
        total_price = bn_stripe_account.bn_cost
        birth_line = 0
        for birth in bn_form['tag_no']:
            child = BnChild.objects.create(tag_no=bn_form['tag_no'][birth_line],
                                           status=bn_form['status'][birth_line],
                                           sex=bn_form['sex'][birth_line],
                                           for_sale=bn_form['for_sale'][birth_line])
            new_bn.births.add(child)
            new_bn.save()
            total_price += bn_stripe_account.bn_child_cost
            birth_line += 1

        bnstripeobject = BnStripeAccount.objects.get(account=attached_service)
        # validate card to update card
        result = validate_card(request, attached_service, bnstripeobject)
        if result['result'] == 'fail':
            return HttpResponse(dumps(result))

        user_detail = request.user.user.all()[0]
        payment_intent = stripe.PaymentIntent.create(
            customer=user_detail.bn_stripe_id,
            amount=total_price,
            currency="gbp",
            payment_method_types=["card"],
            receipt_email=request.user.email,
            stripe_account=bnstripeobject.stripe_acct_id
        )
        new_bn.stripe_payment_token = payment_intent['id']
        new_bn.stripe_payment_source = result['feedback']['id']

        new_bn.save()

        result = {'result': 'success'}
        return HttpResponse(dumps(result))


    else:
        if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
            public_api_key = settings.STRIPE_TEST_PUBLIC_KEY
        else:
            public_api_key = settings.STRIPE_PUBLIC_KEY

        # get next available reg number
        try:
            latest_added = BirthNotification.objects.filter(account=attached_service).latest('bn_number')
            latest_reg = latest_added.reg_no
            reg_ints_re = re.search("[0-9]+", latest_reg)
            bn_number = latest_reg.replace(str(reg_ints_re.group(0)),
                                               str(int(reg_ints_re.group(0)) + 1).zfill(len(reg_ints_re.group(0))))
        except BirthNotification.DoesNotExist:
            bn_number = 'BN123456'
        except AttributeError:
            bn_number = 'BN123456'

        # if reg taken, increment until not taken
        if bn_number == 'BN123456':
            while BirthNotification.objects.filter(account=attached_service, bn_number=bn_number).exists():
                reg_ints_re = re.search("[0-9]+", bn_number)
                bn_number = bn_number.replace(str(reg_ints_re.group(0)),
                                                      str(int(reg_ints_re.group(0)) + 1).zfill(
                                                          len(reg_ints_re.group(0))))

        bn_form = BirthNotificationForm({'bn_number': bn_number})

    return render(request, 'birth_notification_form.html', {'bn_form': bn_form,
                                                            'bn_number': bn_number,
                                                            'public_api_key': public_api_key,
                                                            'bn_stripe_account': bn_stripe_account})

@login_required(login_url="/account/login")
def edit_child(request, id):
    if request.method == 'POST':
        child = BnChild.objects.get(id=id)
        child.tag_no = request.POST.get('tag_no')
        child.status = request.POST.get('status')
        child.sex = request.POST.get('sex')
        child.for_sale = request.POST.get('for_sale')
        child.comments = request.POST.get('comments')
        child.save()
    return redirect('birth_notification', child.births.all()[0].id)


@login_required(login_url="/account/login")
def delete_child(request, id):
    if request.method == 'GET':
        child = BnChild.objects.get(id=id)
        id = child.births.all()[0].id
        child.delete()
    return redirect('birth_notification', id)


@login_required(login_url="/account/login")
def toggle_birth_notification(request, id):
    if request.method == 'GET':
        bn = BirthNotification.objects.get(id=id)
        attached_service = get_main_account(request.user)
        bnstripeobject = BnStripeAccount.objects.get(account=attached_service)

        if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

        # take payment
        payment_confirm = stripe.PaymentIntent.confirm(
            bn.stripe_payment_token,
            payment_method=bn.stripe_payment_source,
            stripe_account=bnstripeobject.stripe_acct_id
        )
        #receipt = stripe.Charge.list(customer=subscription.stripe_id, stripe_account=package.stripe_acct_id, limit=1)

        bn.complete = True
        bn.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


@login_required(login_url="/account/login")
def edit_birth_notification(request, id):
    attached_service = get_main_account(request.user)
    if request.method == 'POST':
        bn = BirthNotification.objects.get(id=id)
        bn.mother = Pedigree.objects.get(account=attached_service,
                                         reg_no=request.POST.get('motherx'))
        bn.father = Pedigree.objects.get(account=attached_service,
                                         reg_no=request.POST.get('fatherx'))
        bn.bn_number = request.POST.get('bn_number')
        bn.dob = request.POST.get('bn_dob')
        bn.comments = request.POST.get('comments')
        bn.save()
    return redirect('birth_notification', bn.id)


@login_required(login_url="/account/login")
def delete_birth_notification(request, id):
    if request.method == 'GET':
        bn = BirthNotification.objects.get(id=id)
        bn.delete()
    return redirect('bn_home')


@login_required(login_url="/account/login")
def validate_bn(request, id):
    # return
    # true == in use
    # false == not in use
    attached_service = get_main_account(request.user)
    bn = BirthNotification.objects.get(account=attached_service, id=id)

    new_bn = list(request.GET.keys())[0]

    # if the bn number is its self, not in use
    if bn.bn_number == list(request.GET.keys())[0]:
        return HttpResponse(False)

    # check if bn number is in use
    try:
        bn_check = BirthNotification.objects.get(account=attached_service, bn_number=new_bn)
    except BirthNotification.DoesNotExist:
        # the bn number is not being used at all, not in use
        return HttpResponse(False)

    # if the bn check is the same as the main bn then it's not in use
    if bn.id == bn_check.id:
        return HttpResponse(False)

    # a bn was found and it's the same as the main bn then it's in use!
    return HttpResponse(True)


def get_account_link(bn_package, attached_service):
    if not attached_service.domain:
        domain = "http://localhost:8000"
    else:
        domain = attached_service.domain
    account_link = stripe.AccountLink.create(
        account=bn_package.stripe_acct_id,
        refresh_url=f'{domain}/birth_notification',
        return_url=f'{domain}/birth_notification',
        type='account_onboarding',
    )
    return account_link


@login_required(login_url='/accounts/login/')
def create_package_on_stripe(request):
    # get strip secret key
    # import stripe key
    if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    attached_service = get_main_account(request.user)
    attached_bolton = attached_service.boltons.get(bolton='1', active=True)
    try:
        bn_package = BnStripeAccount.objects.get(account=attached_service)
    except BnStripeAccount.DoesNotExist:
        bn_package = BnStripeAccount.objects.create(account=attached_service, attached_bolton=attached_bolton)

    if not bn_package.stripe_acct_id:
        # create initial account
        account = stripe.Account.create(
            type="express",
            email=f"{request.user.email}",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_type='company',
            company={
                'name': request.META['HTTP_HOST'],
                "directors_provided": True,
                "executives_provided": True,
            },
            country="GB",
            default_currency="GBP",
        )
        bn_package.stripe_acct_id = account.id

    if not bn_package.stripe_product_id:
        # create product
        product = stripe.Product.create(name='test_name',
                                        stripe_account=bn_package.stripe_acct_id)
        bn_package.stripe_product_id = product.id

    bn_package.save()

    return get_account_link(bn_package, attached_service)


@login_required(login_url="/accounts/login")
def validate_card(request, attached_service, bnstripeobject):
    # get strip secret key
    if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # validate main account created on stripe
    if not bnstripeobject.stripe_acct_id:
        return {'result': 'fail',
                'feedback': "There has been a problem with this Stripe payment, you have not been charged, please try again. If this problem persists, email contact@masys.co.uk"}
    else:
        stripe_id = bnstripeobject.stripe_acct_id

    user_detail = request.user.user.all()[0]

    # create/ update stripe customer
    if user_detail.bn_stripe_id != "":
        try:
            # stripe user already exists
            stripe_customer = stripe.Customer.modify(
                user_detail.bn_stripe_id,
                name=user_detail.user.get_full_name(),
                email=user_detail.user.email,
                stripe_account=bnstripeobject.stripe_acct_id
            )
        except stripe.error.InvalidRequestError:
            # we have a cus is but it doesn't exist in stripe
            stripe_customer = stripe.Customer.create(
                name=user_detail.user.get_full_name(),
                email=user_detail.user.email,
                stripe_account=bnstripeobject.stripe_acct_id
            )
            user_detail.bn_stripe_id = stripe_customer.id
            user_detail.save()
    else:
        stripe_customer = stripe.Customer.create(
            name=user_detail.user.get_full_name(),
            email=user_detail.user.email,
            stripe_account=bnstripeobject.stripe_acct_id
        )
        user_detail.bn_stripe_id = stripe_customer.id
        user_detail.save()

    try:
        payment_method = stripe.Customer.create_source(
            user_detail.bn_stripe_id,
            source=request.POST.get('token[id]'),
            stripe_account=bnstripeobject.stripe_acct_id
        )
        return {'result': 'success',
                'feedback': payment_method}

    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}


def send_payment_error(error):
    body = error.json_body
    err = body.get('error', {})

    feedback = "<strong>Status is:</strong> %s" % error.http_status
    feedback += "<br><strong>Type is:</strong> %s" % err.get('type')
    feedback += "<br><strong>Code is:</strong> %s" % err.get('code')
    feedback += "<br><strong>Message is:</strong> <span class='text-danger'>%s</span>" % err.get('message')
    return feedback