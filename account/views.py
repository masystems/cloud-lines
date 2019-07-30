from django.shortcuts import render, HttpResponse
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import auth
from django.db.models import Q
from django.conf import settings
from .models import UserDetail, AttachedService
from cloud_lines.models import Service
from pedigree.models import Pedigree
from breed.models import Breed
from breed.forms import BreedForm
from breeder.models import Breeder
from breeder.forms import BreederForm
from pedigree.forms import PedigreeForm, AttributeForm, ImagesForm
from money import Money
import random
import string
import stripe
import time
import json


def site_mode(request):

    if request.user.is_authenticated:
        # returns the main account the requesting user is a member of
        attached_service = get_main_account(request.user)

        # returns the user for the main account
        user = UserDetail.objects.get(user=attached_service.user.user)
        user_detail = UserDetail.objects.get(user=request.user)

        attached_services = AttachedService.objects.filter(Q(admin_users=request.user, active=True) | Q(read_only_users=request.user, active=True) | Q(user=user_detail, active=True))

        service = Service.objects.get(id=attached_service.service.id)

        if str(request.user.username) == str(user.user.username):
            editor = True
        elif request.user in attached_service.admin_users.all():
            editor = True
        elif request.user in attached_service.read_only_users.all():
            editor = False
        else:
            editor = False

        if Pedigree.objects.filter(account=attached_service).count() < service.number_of_animals:
            pedigrees = True
        else:
            pedigrees = False

        if attached_service.admin_users.all().count() < service.admin_users:
            admins = True
        else:
            admins = False

        if attached_service.read_only_users.all().count() < service.read_only_users:
            users = True
        else:
            users = False

        if not attached_service.service.multi_breed:
            if Breed.objects.all().count() < 1:
                add_breed = True
            else:
                add_breed = False
        else:
            add_breed = True

        return {'service': attached_service,
                'attached_services': attached_services,
                'add_pedigree': pedigrees,
                'admins': admins,
                'users': users,
                'add_breed': add_breed,
                'editor': editor}

    return {'authenticated': 'no'}


def is_editor(user):
    try:
        main_account = get_main_account(user)
        if user in main_account.admin_users.all():
            return True
        elif user == main_account.user.user:
            return True
        else:
            return False
    except UserDetail.DoesNotExist:
        return False
    except AttachedService.DoesNotExist:
        return False


def get_main_account(user):
    # get detail for logged in user
    user_detail = UserDetail.objects.get(user=user)
    try:
        # get attached service of the primary user
        attached_service = AttachedService.objects.get(id=user_detail.current_service_id, active=True)
    except AttachedService.DoesNotExist:
        # update the attached service to what default
        attached_service = AttachedService.objects.filter(user=user_detail).update(animal_type='Pedigrees',
                                                                               site_mode='mammal',
                                                                               install_available=False,
                                                                               service=Service.objects.get(service_name='Free'),
                                                                               active=True)

    return attached_service


@login_required(login_url="/account/login")
def user_edit(request):
    # this is the additional user customers can add/remove from their service.
    if request.method == 'POST':
        main_account = get_main_account(request.user)
        user_detail = UserDetail.objects.get(user=request.user)
        if request.POST.get('formType') == 'new':
            # generate password
            password = ''.join(
                [random.choice(string.ascii_letters + string.digits + string.punctuation) for n in range(int(10))])

            # create new user
            new_user = User.objects.create_user(username=request.POST.get('register-form-username').lower(),
                                            email=request.POST.get('register-form-email'),
                                            password=password,
                                            first_name=request.POST.get('firstName'),
                                            last_name=request.POST.get('lastName'))

            # update user details
            new_user_detail = UserDetail.objects.create(user=new_user,
                                                    phone='',
                                                    )
            attached_service = AttachedService.objects.filter(user=new_user_detail).update(animal_type='Pedigrees',
                                                                                           install_available=False,
                                                                                           active=True)
            new_user_detail.current_service_id = user_detail.current_service_id
            new_user_detail.save()
            if request.POST.get('status') == 'Editor':
                main_account.admin_users.add(new_user)
            else:
                main_account.read_only_users.add(new_user)

            return HttpResponse(True)

        elif request.POST.get('formType') == 'edit':
            # find user and update name fields
            User.objects.filter(username=request.POST.get('register-form-username'),
                                email=request.POST.get('register-form-email')).update(first_name=request.POST.get('firstName'),
                                                                                      last_name=request.POST.get('lastName'))
            new_user = User.objects.get(username=request.POST.get('register-form-username'),
                                    email=request.POST.get('register-form-email'))
            # remove user from admins and read only users
            main_account.admin_users.remove(new_user)
            main_account.read_only_users.remove(new_user)

            # add user to the request group
            if request.POST.get('status') == 'Editor':
                main_account.admin_users.add(new_user)
            else:
                main_account.read_only_users.add(new_user)

            return HttpResponse(True)

        elif request.POST.get('formType') == 'delete':
            User.objects.get(username=request.POST.get('register-form-username'),
                             email=request.POST.get('register-form-email')).delete()

            return HttpResponse(True)


@login_required(login_url="/account/login")
def update_user(request):
    # where the user can update their own basic information
    if request.method == 'POST':
        # update user and get user object
        user = User.objects.get(username=request.user.username)
        user.first_name = request.POST.get('user-settings-first-name')
        user.last_name = request.POST.get('user-settings-last-name')
        user.email = request.POST.get('user-settings-email')
        # set users password
        user.set_password(request.POST.get('user-settings-password'))
        user.save()

        # update user details
        user_detail = UserDetail.objects.get(user=user)
        user_detail.phone = request.POST.get('user-settings-phone')
        user_detail.save()

        # authenticate to prevent relogging in
        authenticate(username=request.user.username, password=request.POST.get('user-settings-password'))
        login(request, user)

        return HttpResponse(True)

    return HttpResponse(False)


def site_login(request):
    if request.method == 'POST':
        user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            auth.login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'cl_login.html', {'error': 'Username or Password does not exist.'})
    else:
        return render(request, 'cl_login.html')


@login_required(login_url="/account/login")
def logout(request):
    # TO DO need to go to homepage and logout
    # if request.method == 'POST':
    auth.logout(request)
    return redirect('home')


@login_required(login_url="/account/login")
def profile(request):
    context = {}
    #stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        context['public_api_key'] = settings.STRIPE_PUBLIC_KEY
    except AttributeError:
        pass
    context['user_detail'] = UserDetail.objects.get(user=request.user)
    main_account = get_main_account(request.user)

    if request.user == main_account.user and context['user_detail'].current_service.service.service_name != 'Free':
        context['services'] = Service.objects.all().exclude(service_name='Free')
        if main_account.service.service_name != 'Organisation':
            context['recommended'] = Service.objects.filter(id=main_account.service.id+1)
        else:
            context['recommended'] = None

        # billing
        charges = stripe.Charge.list(customer=main_account.user.stripe_id)
        for charge in charges:
            # convert to readable format
            charge_obj = Money(amount=str(charge['amount'] / 100), currency=str(charge['currency']).upper())
            charge['amount'] = charge_obj.format(
                'en_{}'.format(charge['payment_method_details']['card']['country']))
            # convert data to readable format
            date = time.strftime('%d-%m-%Y', time.localtime(charge.created))
            charge['created'] = date
            # get invoice pdf
            invoice = stripe.Invoice.retrieve(charge['invoice'])
            charge['invoice'] = invoice.invoice_pdf

        context['charges'] = charges

        # payment methods
        context['cards'] = stripe.Customer.list_sources(main_account.user.stripe_id, object='card')

    return render(request, 'profile.html', context)


@login_required(login_url="/account/login")
def settings(request):
    user_detail = UserDetail.objects.get(user=request.user)
    custom_fields = user_detail.current_service.custom_fields

    try:
        custom_fields = json.loads(custom_fields)
    except:
        pass
    return render(request, 'settings.html', {'custom_fields': custom_fields})


@user_passes_test(is_editor)
@login_required(login_url="/account/login")
def custom_field_edit(request):
    # this is the additional user customers can add/remove from their service.
    if request.method == 'POST':
        user_detail = UserDetail.objects.get(user=request.user)
        attached_service = AttachedService.objects.get(id=user_detail.current_service_id)
        if user_detail.current_service.custom_fields:
            custom_fields = json.loads(user_detail.current_service.custom_fields)
        else:
            custom_fields = {}

        if request.POST.get('formType') == 'new':
            # create unique key
            for suffix in range(0, len(custom_fields)+2):
                if 'cf_{}'.format(suffix) not in custom_fields:
                    field_key = 'cf_{}'.format(suffix)
                    break

            custom_fields[field_key] = {'id': field_key,
                                        'location': request.POST.get('location'),
                                        'fieldName': request.POST.get('fieldName'),
                                        'fieldType': request.POST.get('fieldType')}
            attached_service.custom_fields = json.dumps(custom_fields)
            attached_service.save()

            # update the model
            if request.POST.get('location') == 'pedigree':
                objects = Pedigree.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breeder':
                objects = Breeder.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breed':
                objects = Breed.objects.filter(account=attached_service)

            for object in objects.all():
                try:
                    if request.POST.get('location') == 'pedigree':
                        object_custom_fields = json.loads(object.attribute.custom_fields)
                    else:
                        object_custom_fields = json.loads(object.custom_fields)
                except json.decoder.JSONDecodeError:
                    object_custom_fields = {}

                object_custom_fields[field_key] = {'id': field_key,
                                                   'location': request.POST.get('location'),
                                                   'fieldName': request.POST.get('fieldName'),
                                                   'fieldType': request.POST.get('fieldType')}

                if request.POST.get('location') == 'pedigree':
                    object.attribute.custom_fields = json.dumps(object_custom_fields)
                    object.attribute.save()
                else:
                    object.custom_fields = json.dumps(object_custom_fields)
                    object.save()
            return HttpResponse(True)

        elif request.POST.get('formType') == 'edit':
            custom_fields[request.POST.get('id')] = {'id': request.POST.get('id'),
                                                     'location': request.POST.get('location'),
                                                     'fieldName': request.POST.get('fieldName'),
                                                     'fieldType': request.POST.get('fieldType')}
            attached_service.custom_fields = json.dumps(custom_fields)
            attached_service.save()

            # update the model
            if request.POST.get('location') == 'pedigree':
                objects = Pedigree.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breeder':
                objects = Breeder.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breed':
                objects = Breed.objects.filter(account=attached_service)

            for object in objects.all():
                try:
                    if request.POST.get('location') == 'pedigree':
                        custom_fields = json.loads(object.attribute.custom_fields)
                    else:
                        custom_fields = json.loads(object.custom_fields)
                except json.decoder.JSONDecodeError:
                    custom_fields = {}

                custom_fields[request.POST.get('id')] = {'id': request.POST.get('id'),
                                                         'location': request.POST.get('location'),
                                                         'fieldName': request.POST.get('fieldName'),
                                                         'fieldType': request.POST.get('fieldType')}
                if request.POST.get('location') == 'pedigree':
                    object.attribute.custom_fields = json.dumps(custom_fields)
                    object.attribute.save()
                else:
                    object.custom_fields = json.dumps(custom_fields)
                    object.save()
            return HttpResponse(True)

        elif request.POST.get('formType') == 'delete':
            custom_fields.pop(request.POST.get('id'), None)
            attached_service.custom_fields = json.dumps(custom_fields)
            attached_service.save()

            # update model
            # update the model
            if request.POST.get('location') == 'pedigree':
                objects = Pedigree.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breeder':
                objects = Breeder.objects.filter(account=attached_service)
            elif request.POST.get('location') == 'breed':
                objects = Breed.objects.filter(account=attached_service)

            for object in objects.all():
                custom_fields_updated = {}
                if request.POST.get('location') == 'pedigree':
                    if object.attribute.custom_fields:
                        for key, val in json.loads(object.attribute.custom_fields).items():
                            if key in custom_fields:
                                custom_fields_updated[key] = val

                    object.attribute.custom_fields = json.dumps(custom_fields_updated)
                    object.attribute.save()
                else:
                    if object.custom_fields:
                        for key, val in json.loads(object.custom_fields).items():
                            if key in custom_fields:
                                custom_fields_updated[key] = val

                    object.custom_fields = json.dumps(custom_fields_updated)
                    object.save()

            return HttpResponse(True)


@user_passes_test(is_editor)
@login_required(login_url="/account/login")
def update_titles(request):
    if request.method == 'POST':
        user_detail = UserDetail.objects.get(user=request.user)
        attached_service = AttachedService.objects.get(id=user_detail.current_service_id)
        attached_service.mother_title = request.POST.get('mother')
        attached_service.father_title = request.POST.get('father')
        attached_service.save()

        return HttpResponse('Done')
    return HttpResponse('Fail')


@user_passes_test(is_editor)
@login_required(login_url="/account/login")
def setup(request):
    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    attributes_form = AttributeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)

    breed_form = BreedForm()
    breeder_form = BreederForm()
    pedigree_form = PedigreeForm()

    return render(request, 'setup_form.html', {'breed_form': breed_form,
                                               'breeder_form': breeder_form,
                                               'pedigree_form': pedigree_form,
                                               'attributes_form': attributes_form,
                                               'image_form': image_form})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('register-form-username')
        raw_password = request.POST.get('register-form-password')
        email = request.POST.get('register-form-email')
        User.objects.create_user(username=username,
                                 email=email,
                                 password=raw_password,
                                 first_name=request.POST.get('register-form-first-name'),
                                 last_name=request.POST.get('register-form-last-name'))
        user = authenticate(username=username, password=raw_password)

        # update user details
        user_detail = UserDetail.objects.create(user=user,
                                                phone=request.POST.get('register-form-phone')
                                                )
        # login
        login(request, user)

        UserDetail.objects.filter(user=user).update(current_service=AttachedService.objects.create(animal_type='Pedigrees',
                                                                                                   site_mode='mammal',
                                                                                                   install_available=False,
                                                                                                   user=user_detail,
                                                                                                   service=Service.objects.get(service_name='Free'),
                                                                                                   active=True))
        # login
        login(request, user)

        email_body = """
        <p><strong>Thank you for registering with Cloudlines!</strong></p>
        
        <p>Now that you have registered you have access to our Free service.</p>
        
        <p><a href="https://cloud-lines.com/dashboard">Click here</a> to go to your new dashboard.</p>
        
        <p>Feel free to contact us about anything and enjoy!</p>"""
        send_mail('Welcome to Cloudlines!', user.get_full_name(), email_body, send_to=user.email)

        send_mail('New site registration', user.get_full_name(), email_body, reply_to=user.email)

        return redirect('order')
    else:
        return render(request, 'login.html')


@csrf_exempt
def username_check(request):
    if request.method == 'POST':
        username = request.POST.get('register-form-username')
        return HttpResponse(User.objects.filter(username=username).exists())


@csrf_exempt
def email_check(request):
    if request.method == 'POST':
        email = request.POST.get('register-form-email')
        return HttpResponse(User.objects.filter(email=email).exists())


@login_required(login_url="/account/login")
@csrf_exempt
def update_card(request):
    user_detail = UserDetail.objects.get(user=request.user)

    # add payment token to user
    try:
        stripe.Customer.modify(
            user_detail.stripe_id,
            source=request.POST.get('id')
        )
    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        feedback = send_payment_error(e)
        result = {'result': 'fail',
                  'feedback': feedback}
        return HttpResponse(json.dumps(result))

    main_account = get_main_account(request.user)
    return HttpResponse(stripe.Customer.list_sources(main_account.user.stripe_id, object='card'))


def send_payment_error(e):
    body = e.json_body
    err = body.get('error', {})

    feedback = "Status is: %s" % e.http_status
    feedback += "<br>Type is: %s" % err.get('type')
    feedback += "<br>Code is: %s" % err.get('code')
    feedback += "<br>Message is: %s" % err.get('message')
    return feedback


def send_mail(subject, name, body,
              send_to='contact@masys.co.uk',
              send_from='contact@masys.co.uk',
              reply_to='contact@masys.co.uk'):

    html_content = render_to_string('mail/email.html', {'name': name,
                                                       'body': body})
    text_content = strip_tags(html_content)

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, send_from, [send_to], reply_to=[reply_to])
    msg.attach_alternative(html_content, "text/html")

    msg.send()

    return
