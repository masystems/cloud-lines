from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Service, Page, Faq, Contact
from account.models import UserDetail, AttachedService
from account.views import get_main_account, send_mail
from django.conf import settings
import json
import stripe
from datetime import datetime, timedelta
from pedigree.models import Pedigree
from breed.models import Breed
from breeder.models import Breeder
from breed_group.models import BreedGroup
from django.db.models import Q


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required(login_url="/account/login")
def dashboard(request):
    main_account = get_main_account(request.user)

    total_pedigrees = Pedigree.objects.filter(account=main_account).count()
    total_breeders = Breeder.objects.filter(account=main_account).count()
    top_pedigrees = Pedigree.objects.filter(account=main_account).order_by('-date_added')[:5]
    breed_groups = BreedGroup.objects.filter(account=main_account).order_by('-date_added')[:5]
    top_breeders = Breeder.objects.filter(account=main_account)

    current_month = datetime.now().month
    date = datetime.now()
    if total_pedigrees > 0 \
            and Breed.objects.filter(account=main_account).exists() \
            and Breeder.objects.filter(account=main_account).exists():
        pedigree_chart = {}
        for month in range(0, 12):
            month_count = Pedigree.objects.filter(account=main_account, date_added__month=current_month-month).count()
            if month != 0:
                date = date.replace(day=1)
                date = date - timedelta(days=1)
            pedigree_chart[date.strftime("%Y-%m")] = {'pedigrees_added': month_count}

        breed_chart = {}
        for breed in Breed.objects.filter(account=main_account):
            breed_chart[breed] = {'male': Pedigree.objects.filter(Q(attribute__breed__breed_name=breed, account=main_account) & Q(sex='male')).count(),
                                   'female': Pedigree.objects.filter(Q(attribute__breed__breed_name=breed, account=main_account) & Q(sex='female')).count()}

    else:
        return redirect('setup')
    # breeders_totals = {}
    # for breeder in top_breeders:
    #     breeders_totals[breeder]['pedigree_count'] = Pedigree.objects.filter(breeder__prefix__exact=breeder).count()
    #     breeders_totals[breeder]['owned_count'] = Pedigree.objects.filter(current_owner__prefix__exact=breeder).count()

    return render(request, 'dashboard.html', {'total_pedigrees': total_pedigrees,
                                              'total_breeders': total_breeders,
                                              'top_pedigrees': top_pedigrees,
                                              'top_breeders': top_breeders,
                                              'breed_groups': breed_groups,
                                              'breed_chart': breed_chart,
                                              'pedigree_chart': pedigree_chart})


def home(request):
    return render(request, 'home.html', {'services': Service.objects.all()})


def about(request):
    return render(request, 'std_page.html', {'content': Page.objects.get(title='About'),
                                             'services': Service.objects.all()})


def extras(request):
    return render(request, 'std_page.html', {'content': Page.objects.get(title='Extras'),
                                             'services': Service.objects.all()})


def faqs(request):
    return render(request, 'faqs.html', {'faqs': Faq.objects.all(),
                                         'services': Service.objects.all()})


def services(request):
    return render(request, 'services.html', {'services': Service.objects.all()})


def contact(request):
    if request.POST:
        name = request.POST.get('name')
        email_address = request.POST.get('email')
        phone = request.POST.get('phone')
        service = request.POST.get('service')
        subject = request.POST.get('subject')
        message_body = request.POST.get('message')

        # send email to user
        email_body = """
                        <p><strong>Thank you for message!</strong></p>
        
                        <p>We have received your message and will be in contact with you soon.</p>
        
                        <p><strong>Copy of your message</strong></p>
        
                        <p>{}</p>
                        <p>{}</p>""".format(subject, message_body)
        send_mail('Cloudlines message confirmation', name, email_body, send_to=email_address)

        # send mail to cloudlines
        email_body = """
                        <p><strong>New message from {}</strong></p>
                        <p>Email: {}</p>
                        <p>Phone: {}</p>
                        <p>Service: {}</p>
                        <p>{}</p>
                        <p>{}</p>""".format(name, email_address, phone, service, subject, message_body)
        send_mail('Cloudlines contact request!', 'Cloudlines Team', email_body, reply_to=email_address)
        try:
            #email.send(fail_silently=False)
            email_obj = Contact.objects.create(name=name,
                                               email=email_address,
                                               phone=phone,
                                               service=service,
                                               subject=subject,
                                               message=message_body)
            email_obj.save()
            message = {'message': "Thank you for your email, we'll be in touch soon!"}
        except:
            message = {'message': "Something went wrong, but we're working on it!"}

        return HttpResponse(json.dumps(message), content_type='application/json')
    else:
        return render(request, 'contact.html', {'services': Service.objects.all()})


@login_required(login_url="/account/login")
def order(request):
    context = {}
    # import stripe key
    context['public_api_key'] = settings.STRIPE_PUBLIC_KEY

    # get user detail object
    context['user_detail'] = UserDetail.objects.get(user=request.user)

    if 'id' in request.GET:
        # get service the user wants to upgrade to
        context['requested_service'] = Service.objects.get(id=request.GET['id'])

    if 'upgrade' in request.GET:
        try:
            context['customer'] = stripe.Customer.retrieve(context['user_detail'].stripe_id)
        except stripe.error.InvalidRequestError:
            pass

        # get the attached_service to upgrade
        if AttachedService.objects.filter(user=UserDetail.objects.get(user=request.user),
                                          id=request.GET['upgrade']).exists():
            context['attached_service_upgrade'] = request.GET['upgrade']

    context['services'] = Service.objects.filter(active=True)

    return render(request, 'order.html', context)


@login_required(login_url="/account/login")
def order_service(request):
    if request.POST:
        # attach_services = AttachedService.objects.all()
        # attach_services.delete()
        user_detail = UserDetail.objects.get(user=request.user)
        service = Service.objects.get(price_per_month=request.POST.get('checkout-form-service'))

        # if upgade
        if request.POST.get('checkout-form-upgrade'):
            print(request.POST.get('checkout-form-animal-type'))
            try:
                attached_service = AttachedService.objects.filter(user=user_detail,
                                                                  id=request.POST.get('checkout-form-upgrade')).update(animal_type=request.POST.get('checkout-form-animal-type'),
                                                                                                                       site_mode=request.POST.get('checkout-form-site-mode'),
                                                                                                                       install_available=False,
                                                                                                                       service=service,
                                                                                                                       increment=request.POST.get('checkout-form-payment-inc').lower(),
                                                                                                                       active=False)
            except AttachedService.DoesNotExist:
                pass
        else:
            # create new attached service details object
            attached_service = AttachedService.objects.create(user=user_detail,
                                                              animal_type=request.POST.get('checkout-form-animal-type'),
                                                              site_mode=request.POST.get('checkout-form-site-mode'),
                                                              install_available=False,
                                                              service=service,
                                                              increment=request.POST.get('checkout-form-payment-inc').lower(),
                                                              active=False)

    return HttpResponse(json.dumps(attached_service.id))


@login_required(login_url="/account/login")
def order_billing(request):
    if request.POST:
        user_detail = UserDetail.objects.get(user=request.user)

        if not user_detail.stripe_id:
            # create stripe user
            stripe.api_key = settings.STRIPE_SECRET_KEY
            customer = stripe.Customer.create(
                name=request.POST.get('checkout-form-billing-name'),
                email=request.POST.get('checkout-form-billing-email'),

                phone=request.POST.get('checkout-form-billing-phone'),
                address={'line1': request.POST.get('checkout-form-billing-add1'),
                         'city': request.POST.get('checkout-form-billing-city'),
                         'country': request.POST.get('checkout-form-billing-country'),
                         'line2': request.POST.get('checkout-form-billing-add2'),
                         'postal_code': request.POST.get('checkout-form-billing-post-code')}
            )
            customer_id = customer['id']
            # update user datail
            UserDetail.objects.filter(user=request.user).update(stripe_id=customer_id)
        else:
            stripe.Customer.modify(
                user_detail.stripe_id,
                name=request.POST.get('checkout-form-billing-name'),
                email=request.POST.get('checkout-form-billing-email'),

                phone=request.POST.get('checkout-form-billing-phone'),
                address={'line1': request.POST.get('checkout-form-billing-add1'),
                         'city': request.POST.get('checkout-form-billing-city'),
                         'country': request.POST.get('checkout-form-billing-country'),
                         'line2': request.POST.get('checkout-form-billing-add2'),
                         'postal_code': request.POST.get('checkout-form-billing-post-code')}
            )

    return HttpResponse('done')


@login_required(login_url="/account/login")
def order_subscribe(request):
    user_detail = UserDetail.objects.get(user=request.user)
    attach_service = AttachedService.objects.get(id=request.POST.get('attached_service_id'), user=user_detail, active=False)

    # add payment token to user
    try:
        stripe.Customer.modify(
            user_detail.stripe_id,
            source=request.POST.get('token[id]')
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


    # update the users attached service to be active
    attach_service.active = True

    if attach_service.increment == 'yearly':
        plan = attach_service.service.yearly_id
    else:
        plan = attach_service.service.monthly_id

    # update existing subscription if it exists
    if attach_service.subscription_id:
        subscription = stripe.Subscription.retrieve(attach_service.subscription_id)
        #stripe.Subscription.delete(attach_service.subscription_id)
        stripe.Subscription.modify(
            attach_service.subscription_id,
            cancel_at_period_end=False,
            items=[{
                'id': subscription['items']['data'][0].id,
                'plan': plan,
            }]
        )

    # subscribe user to the selected plan
    subscription = stripe.Subscription.create(
        customer=user_detail.stripe_id,
        items=[
            {
                "plan": plan,
            },
        ]
    )

    if subscription:
        attach_service.subscription_id = subscription['id']
        attach_service.save()
    else:
        return HttpResponse(json.dumps({'Error': 'Something went wrong, please contact us.'}))

    invoice = stripe.Invoice.list(customer=user_detail.stripe_id, subscription=subscription.id, limit=1)
    receipt = stripe.Charge.list(customer=user_detail.stripe_id)

    result = {'result': 'success',
              'invoice': invoice.data[0].invoice_pdf,
              'receipt': receipt.data[0].receipt_url}

    # send confirmation email
    body = """
        Congratulations on purchasing a new Cloudlines {} service!
        To access your new service click <a href="https://cloud-lines.co.uk/dashboard"> HERE</a>. You should
        find everything you need to get started there but do let is know if you have any questions.
    """.format(attach_service.service.service_name,)
    send_mail('New subscription!', request.user, body, send_to=request.user.email)

    # set new default attached service
    UserDetail.objects.filter(user=request.user).update(current_service=attach_service)

    # delete dead attached services
    AttachedService.objects.filter(user=user_detail, active=False).delete()

    return HttpResponse(json.dumps(result))


def send_payment_error(e):
    body = e.json_body
    err = body.get('error', {})

    feedback = "Status is: %s" % e.http_status
    feedback += "<br>Type is: %s" % err.get('type')
    feedback += "<br>Code is: %s" % err.get('code')
    feedback += "<br>Message is: %s" % err.get('message')
    return feedback


def activate_primary_account(request, service):
    user_details = UserDetail.objects.get(user=request.user)
    try:
        primary_account = AttachedService.objects.get(user=user_details, id=service)
    except AttachedService.DoesNotExist:
        return redirect('dashboard')

    if AttachedService.objects.filter(id=service, admin_users=request.user, active=True).exists()\
            or AttachedService.objects.filter(id=service, read_only_users=request.user, active=True).exists() \
            or AttachedService.objects.filter(id=service, user=user_details, active=True).exists():
        UserDetail.objects.filter(user=request.user).update(current_service=primary_account)

    return redirect('dashboard')

