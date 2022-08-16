from django.shortcuts import render, redirect, HttpResponse
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
import re
import stripe


# Create your views here.
class BirthNotificationBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)
        context['birth_notifications'] = BirthNotification.objects.filter(account=context['attached_service'])
        context['latest'] = BirthNotification.objects.filter(account=context['attached_service'])[:10]

        return context


class BnHome(BirthNotificationBase):
    template_name = 'bn_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_living'] = BnChild.objects.filter(status="alive").count()
        context['total_deceased'] = BnChild.objects.filter(status="deceased").count()
        context['approvals'] = BirthNotification.objects.filter(complete=False)

        if self.request.user.is_superuser:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

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
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    attached_service = get_main_account(request.user)

    if request.method == 'POST':
        bn_form = BirthNotificationForm(request.POST or None)
        if bn_form.is_valid():
            new_bn = BirthNotification()
            ### mother ###
            try:
                new_bn.mother = Pedigree.objects.get(account=attached_service,
                                                      reg_no=request.POST.get('motherx'))
            except:
                print('Not a valid mother')

            ### father ###
            try:
                new_bn.father = Pedigree.objects.get(account=attached_service,
                                                      reg_no=request.POST.get('fatherx'))
            except:
                pass
            new_bn.user = request.user
            new_bn.account = attached_service
            new_bn.bn_number = bn_form['bn_number'].value().strip()
            new_bn.comments = bn_form['comments'].value().strip()
            new_bn.save()

            # births
            bn_child_form = dict(request.POST.lists())
            birth_line = 0
            for birth in bn_child_form['tag_no']:
                child = BnChild.objects.create(tag_no=bn_child_form['tag_no'][birth_line],
                                               status=bn_child_form['status'][birth_line],
                                               sex=bn_child_form['sex'][birth_line])
                new_bn.births.add(child)
                new_bn.save()
                birth_line += 1

            return redirect('bn_home')


    else:
        if request.user.is_superuser:
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
                                                            'public_api_key': public_api_key})

@login_required(login_url="/account/login")
def edit_child(request, id):
    if request.method == 'POST':
        child = BnChild.objects.get(id=id)
        child.tag_no = request.POST.get('tag_no')
        child.status = request.POST.get('status')
        child.sex = request.POST.get('sex')
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
        if bn.complete:
            bn.complete = False
        else:
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
    bn = BirthNotification.objects.get(id=id)

    new_bn = list(request.GET.keys())[0]

    # if the bn number is its self, not in use
    if bn.bn_number == list(request.GET.keys())[0]:
        return HttpResponse(False)

    # check if bn number is in use
    try:
        bn_check = BirthNotification.objects.get(bn_number=new_bn)
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
    if request.user.is_superuser:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    attached_service = get_main_account(request.user)
    attached_bolton = AttachedBolton.objects.get(bolton='1', active=True)
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
                'name': 'test_name',
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