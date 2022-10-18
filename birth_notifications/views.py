from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor,\
    get_main_account,\
    has_permission,\
    redirect_2_login,\
    get_stripe_secret_key,\
    get_stripe_public_key
from account.models import AttachedBolton, BnStripe
from .models import BirthNotification, BnChild
from .forms import BirthNotificationForm
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

        return context


class BnHome(BirthNotificationBase):
    template_name = 'bn_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['birth_notifications'] = BirthNotification.objects.filter(account=context['attached_service'], paid=True)
        context['latest'] = context['birth_notifications'].filter(account=context['attached_service'], paid=True).order_by('-id')[:10]

        context['total_living'] = context['birth_notifications'].filter(births__status="alive", paid=True).count()
        context['total_deceased'] = context['birth_notifications'].filter(births__status="deceased", paid=True).count()
        context['approvals'] = BirthNotification.objects.filter(account=context['attached_service'], paid=True , complete=False)

        stripe.api_key = get_stripe_secret_key(self.request)

        if self.request.user == context['attached_service'].user.user:
            try:
                context['bn_stripe_account'] = BnStripe.objects.get(account=context['attached_service'])
            except BnStripe.DoesNotExist:
                context['account_link'] = create_package_on_stripe(self.request)
                context['bn_stripe_account'] = BnStripe.objects.get(account=context['attached_service'])

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

        stripe.api_key = get_stripe_secret_key(self.request)

        context['bn_stripe_account'] = BnStripe.objects.get(account=context['attached_service'])

        # get bn price
        if context['bn_stripe_account'].bn_cost_id:
            context['bn_cost'] = stripe.Price.retrieve(
                context['bn_stripe_account'].bn_cost_id,
                stripe_account=context['bn_stripe_account'].stripe_acct_id
            ).unit_amount
        else:
            context['bn_cost'] = 0
        # get child price
        if context['bn_stripe_account'].bn_child_cost_id:
            context['bn_child_cost'] = stripe.Price.retrieve(
                context['bn_stripe_account'].bn_child_cost_id,
                stripe_account=context['bn_stripe_account'].stripe_acct_id
            ).unit_amount
        else:
            context['bn_child_cost'] = 0
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

    stripe.api_key = get_stripe_secret_key(request)

    attached_service = get_main_account(request.user)

    bn_stripe_account = BnStripe.objects.get(account=attached_service)

    bn_stripe_account.bn_cost_id = stripe.Price.create(
        nickname="BN Price",
        unit_amount=int(float(request.POST.get('bncost')) * 100),
        currency="gbp",
        product=bn_stripe_account.bn_stripe_product_id,
        stripe_account=bn_stripe_account.stripe_acct_id
    ).id

    bn_stripe_account.bn_child_cost_id = stripe.Price.create(
        nickname="BN Child Price",
        unit_amount=int(float(request.POST.get('bnccost')) * 100),
        currency="gbp",
        product=bn_stripe_account.bn_stripe_product_id,
        stripe_account=bn_stripe_account.stripe_acct_id
    ).id
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
        bn_stripe_account = BnStripe.objects.get(account=attached_service)
    except BnStripe.DoesNotExist:
        bn_stripe_account = False

    stripe.api_key = get_stripe_secret_key(request)

    # get bn price
    if bn_stripe_account.bn_cost_id not in ["", None]:
        bn_cost = stripe.Price.retrieve(
            bn_stripe_account.bn_cost_id,
            stripe_account=bn_stripe_account.stripe_acct_id
        ).unit_amount
    else:
        bn_cost = 0
    # get child price
    if bn_stripe_account.bn_child_cost_id not in ["", None]:
        bn_child_cost = stripe.Price.retrieve(
            bn_stripe_account.bn_child_cost_id,
            stripe_account=bn_stripe_account.stripe_acct_id
        ).unit_amount
    else:
        bn_child_cost = 0

    if request.method == 'POST':
        #bn_form = BirthNotificationForm(request.POST or None)
        bn_form = request.POST

        new_bn = BirthNotification()
        ### mother ###
        try:
            new_bn.mother = Pedigree.objects.get(account=attached_service,
                                                  reg_no=bn_form['motherx'])
        except:
            pass

        ### father ###
        try:
            new_bn.father = Pedigree.objects.get(account=attached_service,
                                                  reg_no=bn_form['fatherx'])
        except:
            pass

        new_bn.user = request.user
        new_bn.account = attached_service
        # not currently validating against other bn numbers on same instance
        new_bn.bn_number = bn_form['bn_number']
        if bn_form['dob'] != '':
            try:
                new_bn.dob = bn_form['dob']
            except KeyError:
                # no date added
                pass
        try:
            new_bn.comments = bn_form['comments']
        except KeyError:
            # no comment added
            pass

        # needs to be moved to after adding children
        try:
            new_bn.save()
        except IntegrityError:
            result = {'result': 'fail',
                      'feedback': f'BN Number: {bn_form["bn_number"]} already in use!'}
            return HttpResponse(dumps(result))

        # births and calc total
        birth_line = 0
        bn_form_dict = dict(bn_form)
        for birth in bn_form_dict['tag_no']:
            child = BnChild.objects.create(tag_no=bn_form_dict['tag_no'][birth_line],
                                           status=bn_form_dict['status'][birth_line],
                                           sex=bn_form_dict['sex'][birth_line],
                                           for_sale=bn_form_dict['for_sale'][birth_line])
            new_bn.births.add(child)
            new_bn.save()
            birth_line += 1
        new_bn.save()

        # process payment
        if bn_stripe_account.bn_cost_id or bn_stripe_account.bn_child_cost_id:
            user_detail = request.user.user.all()[0]

            # get or create customer
            if not user_detail.bn_stripe_id:
                customer = stripe.Customer.create(
                    email=user_detail.user.email,
                    stripe_account=bn_stripe_account.stripe_acct_id
                )
                user_detail.bn_stripe_id = customer['id']
            else:
                customer = stripe.Customer.retrieve(user_detail.bn_stripe_id,
                                                    stripe_account=bn_stripe_account.stripe_acct_id)

            # create session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        "price": bn_stripe_account.bn_cost_id,
                        "quantity": 1,
                    },
                    {
                        "price": bn_stripe_account.bn_child_cost_id,
                        "quantity": birth_line,
                    },
                ],
                mode='payment',
                customer=customer.id,
                success_url=f"http://{request.META['HTTP_HOST']}/birth_notification/birth_notification_paid/{new_bn.id}",
                cancel_url=f"http://{request.META['HTTP_HOST']}/birth_notification",
                stripe_account=bn_stripe_account.stripe_acct_id,
            )
            new_bn.stripe_payment_token = session['id']
            new_bn.save()
            return redirect(session.url, code=303)
        else:
            # payment required, set paid to true to ensure visibility
            new_bn.paid = True
            new_bn.save()
            return redirect('birth_notification', new_bn.id)

    else:
        public_api_key = get_stripe_public_key(request)

        # get next available reg number
        try:
            latest_added = BirthNotification.objects.filter(account=attached_service).latest('bn_number')
            latest_reg = latest_added.bn_number
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
                                                            'bn_stripe_account': bn_stripe_account,
                                                            'bn_cost': bn_cost,
                                                            'bn_child_cost': bn_child_cost})

@login_required(login_url="/account/login")
def birth_notification_paid(request, id):
    # return view from stripe on sucessful payment for a new birth notification
    BirthNotification.objects.filter(id=id).update(paid=True)
    return redirect('birth_notification', id)


@login_required(login_url="/account/login")
def enable_bn(request, id):
    # return view from stripe on successful payment of enabling the bn bolton
    attached_service = get_main_account(request.user)
    new_bolton = AttachedBolton.objects.get(id=id)
    new_bolton.active = True
    new_bolton.save()
    attached_service.boltons.add(new_bolton)

    # send confirmation email
    #     body = f"""<p>This email confirms the successful creation of your new Cloud-Lines bolton.
    #
    #                     <ul>
    #                     <li>Bolton: {bolton['name']}</li>
    #                     <li>Monthly Cost: £{bolton['price']}</li>
    #                     </ul>
    #
    #                     <p>Thank you for purchasing this boloton. Please contact us if you need anything - contact@masys.co.uk</p>
    #
    #                     """
    # send_mail(f"New Bolton Added: {bolton['name']}",
    #            request.user.get_full_name(), body,
    #            send_to=request.user.email)

    return redirect('settings')


@login_required(login_url="/account/login")
def edit_child(request, id):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

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
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    if request.method == 'GET':
        child = BnChild.objects.get(id=id)
        id = child.births.all()[0].id
        child.delete()
    return redirect('birth_notification', id)


@login_required(login_url="/account/login")
def approve_birth_notification(request, id):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    if request.method == 'GET':
        bn = BirthNotification.objects.get(id=id)
        attached_service = get_main_account(request.user)

        bn.complete = True
        bn.save()
    return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


@login_required(login_url="/account/login")
def edit_birth_notification(request, id):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

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
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    if request.method == 'GET':
        attached_service = get_main_account(request.user)
        bnstripeobject = BnStripe.objects.get(account=attached_service)
        bn = BirthNotification.objects.get(id=id)

        if bnstripeobject.bn_cost_id or bnstripeobject.bn_child_cost_id:
            stripe.api_key = get_stripe_secret_key(request)
            # submit refund
            session = stripe.checkout.Session.retrieve(
                bn.stripe_payment_token,
                stripe_account=bnstripeobject.stripe_acct_id
            )

            if session['payment_status'] == 'paid':
                payment_intent = stripe.PaymentIntent.retrieve(
                    session.payment_intent,
                    stripe_account=bnstripeobject.stripe_acct_id
                )

                # create refund
                stripe.Refund.create(
                    charge=payment_intent['charges']['data'][0]['id'],
                    stripe_account=bnstripeobject.stripe_acct_id
                )
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
    public_api_key = get_stripe_secret_key(request)

    attached_service = get_main_account(request.user)
    attached_bolton = attached_service.boltons.get(bolton='1', active=True)
    try:
        bn_package = BnStripe.objects.get(account=attached_service)
    except BnStripe.DoesNotExist:
        bn_package = BnStripe.objects.create(account=attached_service, attached_bolton=attached_bolton)

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

    if not bn_package.bn_stripe_product_id:
        # create product
        product = stripe.Product.create(name='Birth Notification',
                                        stripe_account=bn_package.stripe_acct_id)
        bn_package.bn_stripe_product_id = product.id

    bn_package.save()

    return get_account_link(bn_package, attached_service)


def validate_bn_number(request):
    if request.POST:
        print(request.POST.get('bn_number'))
    return JsonResponse({'result': BirthNotification.objects.filter(bn_number=request.POST.get('bn_number')).exists()})