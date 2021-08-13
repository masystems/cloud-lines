from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import MultiValueDictKeyError
from .models import Service, Page, Gallery, Faq, Testimonial, LargeTierQueue, Blog
from .forms import ContactForm, BlogForm
from account.models import UserDetail, AttachedService
from account.views import get_main_account, send_mail, has_permission, redirect_2_login
from django.conf import settings
import json
import stripe
from datetime import datetime, timedelta
from pedigree.models import Pedigree
from breed.models import Breed
from breeder.models import Breeder
from breed_group.models import BreedGroup
from django.db.models import Q
from re import match
import requests


@login_required(login_url="/account/login")
def dashboard(request):
    main_account = get_main_account(request.user)
    if main_account.domain and not match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return HttpResponseRedirect(main_account.domain)

    total_pedigrees = Pedigree.objects.filter(account=main_account).exclude(state='unapproved').count()
    top_pedigrees = Pedigree.objects.filter(account=main_account).order_by('-date_added').exclude(state='unapproved')[:5]
    breed_groups = BreedGroup.objects.filter(account=main_account).order_by('-date_added').exclude(state='unapproved')[:5]
    latest_breeders = Breeder.objects.filter(account=main_account).order_by('-id')[:5]

    current_month = datetime.now().month
    date = datetime.now()
    if total_pedigrees > 0 \
            and Breed.objects.filter(account=main_account).exists() \
            and len(latest_breeders) > 0:
        pedigree_chart = {}
        for month in range(0, 12):
            month_count = Pedigree.objects.filter(account=main_account, date_of_registration__month=current_month-month).count()
            if month != 0:
                date = date.replace(day=1)
                date = date - timedelta(days=1)
            pedigree_chart[date.strftime("%Y-%m")] = {'pedigrees_added': month_count}

        breed_chart = {}
        for breed in Breed.objects.filter(account=main_account):
            breed_chart[breed] = {'male': Pedigree.objects.filter(Q(breed__breed_name=breed, account=main_account) & Q(sex='male')).exclude(state='unapproved').count(),
                                   'female': Pedigree.objects.filter(Q(breed__breed_name=breed, account=main_account) & Q(sex='female')).exclude(state='unapproved').count()}

    else:
        return redirect('welcome')

    # updates
    # try:
    #     get_updates_json = requests.get('https://cloud-lines.com/api/updates/?format=json')
    #     updates = get_updates_json.json()
    #     updates = updates['results']
    #     update_card_size = 44 * len(updates)
    # except (ConnectionError, KeyError):
    #     updates = {}
    #     update_card_size = 44

    return render(request, 'dashboard.html', {'total_pedigrees': total_pedigrees,
                                              'top_pedigrees': top_pedigrees,
                                              'latest_breeders': latest_breeders,
                                              'breed_groups': breed_groups,
                                              'breed_chart': breed_chart,
                                              'pedigree_chart': pedigree_chart,})
                                              # 'updates': updates,
                                              # 'update_card_size': update_card_size})


def home(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'home.html', {'services': Service.objects.all(),
                                         'testimonials': Testimonial.objects.all(),
                                         'images': Gallery.objects.all()})


def about(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'std_page.html', {'content': Page.objects.get(title='About'),
                                             'services': Service.objects.all()})


def extras(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'std_page.html', {'content': Page.objects.get(title='Extras'),
                                             'services': Service.objects.all()})


def faqs(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'faqs.html', {'faqs': Faq.objects.all(),
                                         'services': Service.objects.all()})


def services(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'services.html', {'services': Service.objects.all()})


def blog(request):
    if request.POST:
        print(request.POST)
        if request.POST['articleID'] == '0':
            # new article
            new_blog = Blog.objects.create(title=request.POST['title'],
                                           content=request.POST['content'])
            try:
                new_blog.video = request.POST['video']
            except MultiValueDictKeyError:
                # no video link
                pass

            try:
                new_blog.image = request.FILES['image']
            except MultiValueDictKeyError:
                # no image
                pass

            new_blog.save()
        else:
            blog = Blog.objects.get(id=request.POST['articleID'])
            blog.title = request.POST['title']
            blog.content = request.POST['content']
            try:
                blog.video = request.POST['video']
            except MultiValueDictKeyError:
                # no video link
                pass

            blog.save()

    blog_form = BlogForm()
    articles = Blog.objects.all()
    return render(request, 'blog.html', {'articles': articles,
                                         'blog_form': blog_form})


def blog_article(request, id, title):
    article = Blog.objects.get(id=id)
    return render(request, 'single_blog.html', {'article': article})


@login_required(login_url="/account/login")
def delete_blog(request, id):
    if request.POST:
        if request.user.is_superuser:
            Blog.objects.get(id=id).delete()

    blog_form = BlogForm()
    articles = Blog.objects.all()
    return render(request, 'blog.html', {'articles': articles,
                                         'blog_form': blog_form})


def contact(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return HttpResponseRedirect('https://cloud-lines.com/contact')
    contact_form = ContactForm(request.POST or None, request.FILES or None)
    if request.POST:
        if contact_form.is_valid():
            contact_form.save()

            name = request.POST.get('name')
            email_address = request.POST.get('email')
            phone = request.POST.get('phone')
            service = request.POST.get('service')
            service = Service.objects.get(id=service)
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
                            <p>{}</p>""".format(name, email_address, phone, service.service_name, subject, message_body)
            send_mail('Cloudlines contact request!', 'Cloudlines Team', email_body, reply_to=email_address)

            message = {'message': "Thank you for your email, we'll be in touch soon!"}

            return HttpResponse(json.dumps(message), content_type='application/json')
        else:
            message = {'message': "Oops! Looks like the form wasn't valid."}

            return HttpResponse(json.dumps(message), content_type='application/json')
    else:
        contact_form = ContactForm()
        return render(request, 'contact.html', {'services': Service.objects.all(),
                                                'contact_form': contact_form})


def privacy_policy(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'std_page.html', {'content': Page.objects.get(title='privacy policy'),
                                             'services': Service.objects.all()})


def gdpr(request):
    if match('(.*).cloud-lines.com', request.META['HTTP_HOST']):
        return redirect('dashboard')
    return render(request, 'std_page.html', {'content': Page.objects.get(title='gdpr'),
                                             'services': Service.objects.all()})

@login_required(login_url="/account/login")
def order(request, service=None):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': False, 'breed_admin': False}, []):
            return redirect_2_login(request)
    
    context = {}
    # import stripe key
    if request.user.is_superuser:
        context['public_api_key'] = settings.STRIPE_TEST_PUBLIC_KEY
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        context['public_api_key'] = settings.STRIPE_PUBLIC_KEY
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # get user detail object
    context['user_detail'] = UserDetail.objects.get(user=request.user)

    if 'id' in request.GET:
        # get service the user wants to upgrade to
        context['requested_service'] = Service.objects.get(id=request.GET['id'])
    elif service:
        context['requested_service'] = Service.objects.get(id=service)

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
        # import stripe key
        if request.user.is_superuser:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

        user_detail = UserDetail.objects.get(user=request.user)
        service = Service.objects.get(price_per_month=request.POST.get('checkout-form-service'))

        if request.POST.get('checkout-form-sub-domain'):
            domain = 'https://{}.cloud-lines.com'.format(request.POST.get('checkout-form-sub-domain'))
        else:
            domain = ''

        # if upgade
        if request.POST.get('checkout-form-upgrade'):
            try:
                attached_service = AttachedService.objects.filter(user=user_detail,
                                                                  id=request.POST.get('checkout-form-upgrade')).update(animal_type=request.POST.get('checkout-form-animal-type'),
                                                                                                                       site_mode=request.POST.get('checkout-form-site-mode'),
                                                                                                                       domain=domain,
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
                                                              domain=domain,
                                                              install_available=False,
                                                              service=service,
                                                              increment=request.POST.get('checkout-form-payment-inc').lower(),
                                                              active=False)

    return HttpResponse(json.dumps(attached_service.id))


@login_required(login_url="/account/login")
def order_billing(request):
    if request.POST:
        if request.user.is_superuser:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

        user_detail = UserDetail.objects.get(user=request.user)

        if not user_detail.stripe_id:
            # create stripe user
            if request.user.is_superuser:
                stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
            else:
                stripe.api_key = settings.STRIPE_SECRET_KEY
            customer = stripe.Customer.create(
                name=request.POST.get('checkout-form-billing-name'),
                email=request.POST.get('checkout-form-billing-email'),

                phone=request.POST.get('checkout-form-billing-phone'),
                address={'postal_code': request.POST.get('checkout-form-billing-post-code')}
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
                address={'postal_code': request.POST.get('checkout-form-billing-post-code')}
            )

    return HttpResponse('done')


@login_required(login_url="/account/login")
def order_subscribe(request):
    user_detail = UserDetail.objects.get(user=request.user)
    attached_service = AttachedService.objects.get(id=request.POST.get('attached_service_id'), user=user_detail, active=False)
    large_tier = ['Small Society', 'Large Society', 'Organisation']

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
    attached_service.active = True

    if request.user.is_superuser:
        if attached_service.increment == 'yearly':
            plan = attached_service.service.yearly_test_id
        else:
            plan = attached_service.service.monthly_test_id
    else:
        if attached_service.increment == 'yearly':
            plan = attached_service.service.yearly_id
        else:
            plan = attached_service.service.monthly_id

    # update existing subscription if it exists
    if attached_service.subscription_id:
        subscription = stripe.Subscription.retrieve(attached_service.subscription_id)
        stripe.Subscription.modify(
            attached_service.subscription_id,
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
        attached_service.subscription_id = subscription['id']
        attached_service.save()
    else:
        return HttpResponse(json.dumps({'Error': 'Something went wrong, please contact us.'}))

    invoice = stripe.Invoice.list(customer=user_detail.stripe_id, subscription=subscription.id, limit=1)
    receipt = stripe.Charge.list(customer=user_detail.stripe_id)

    result = {'result': 'success',
              'invoice': invoice.data[0].invoice_pdf,
              'receipt': receipt.data[0].receipt_url}

    # send confirmation email
    if attached_service.service.service_name in large_tier:
        body = """
            Congratulations on purchasing a new Cloudlines {} service!
            Your new service is building now. We will send you another email once it's built and ready to access.
            
            Remember you can always use the in built feature to import any existing data but if you would prefer you can
            <a href="https://cloud-lines.com/contact">Contact us</a> and we'd be happy to help.
            
        """.format(attached_service.service.service_name, )
    else:
        body = """
            Congratulations on purchasing a new Cloudlines {} service!
            To access your new service click <a href="https://cloud-lines.com/dashboard"> HERE</a>. You should
            find everything you need to get started there but do let is know if you have any questions.
        """.format(attached_service.service.service_name,)
    send_mail('New subscription!', request.user, body, send_to=request.user.email)
    send_mail('New subscription!', request.user, body, reply_to=request.user.email)

    # set new default attached service
    UserDetail.objects.filter(user=request.user).update(current_service=attached_service)

    # delete dead attached services
    AttachedService.objects.filter(user=user_detail, active=False).delete()

    if attached_service.service.service_name in large_tier:
        queue_item = LargeTierQueue.objects.create(subdomain=request.POST.get('subdomain'), user=request.user, user_detail=user_detail, attached_service=attached_service)
        result['tier'] = 'large'
        result['build_id'] = queue_item.id

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
        primary_account = AttachedService.objects.get(id=service)
    except AttachedService.DoesNotExist:
        return redirect('dashboard')

    if AttachedService.objects.filter(id=service, admin_users=request.user, active=True).exists()\
            or AttachedService.objects.filter(id=service, read_only_users=request.user, active=True).exists() \
            or AttachedService.objects.filter(id=service, user=user_details, active=True).exists():
        UserDetail.objects.filter(user=request.user).update(current_service=primary_account)

    return redirect('dashboard')


def know_more(request):
    if request.POST:
        body = """
            Contact request: {}
            """.format(request.POST.get('contact'))
        send_mail('Contact Request', 'Cloudlines Team', body)
    return HttpResponse(True)


def get_build_status(request):
    if request.method == 'POST':
        queue_id = request.POST.get('build_id')
        queue_item = LargeTierQueue.objects.get(id=queue_id)
        if queue_item.build_state == 'complete':
            status = {'status': 'complete'}
        else:
            status = {'status': queue_item.build_status}

        status['percent'] = queue_item.percentage_complete
        return HttpResponse(json.dumps(status))


def robots(request):
    return render(request, 'robots.txt')