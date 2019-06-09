from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Service, Page, Faq, Contact
from account.models import UserDetail, AttachedService
from django.conf import settings
import json
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

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


# def contact(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         email_address = request.POST.get('email')
#         phone = request.POST.get('phone')
#         service = request.POST.get('service')
#         subject = request.POST.get('subject')
#         message_body = request.POST.get('message')
#         email = EmailMessage(
#             subject,
#             "From: {},\nPhone: {},\nService: {},\nMessage: {}".format(name,
#                                                                       phone,
#                                                                       service,
#                                                                       message_body),
#             'contact@cmdlb.com',
#             ['marco@masys.co.uk', 'adam@masys.co.uk'],
#             reply_to=[email_address],
#         )
#         try:
#             email.send(fail_silently=False)
#             email_obj = Contact.objects.create(name=name,
#                                                email=email_address,
#                                                phone=phone,
#                                                service=service,
#                                                subject=subject,
#                                                message=message_body)
#             email_obj.save()
#         except:
#             redirect('result', 'fail')
#
#         return redirect('result', 'success')
#     else:
#         return render(request, 'contact.html', {'services': Service.objects.all()})


def contact(request):
    if request.POST:
        name = request.POST.get('name')
        email_address = request.POST.get('email')
        phone = request.POST.get('phone')
        service = request.POST.get('service')
        subject = request.POST.get('subject')
        message_body = request.POST.get('message')

        # email = EmailMessage(
        #     subject,
        #     "From: {},\nPhone: {},\nService: {},\nMessage: {}".format(name,
        #                                                               phone,
        #                                                               service,
        #                                                               message_body),
        #     'contact@cmdlb.com',
        #     ['marco@masys.co.uk'],
        #     reply_to=[email_address],
        # )
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
    return render(request, 'order.html', {'services': Service.objects.all(),
                                          'user_detail': UserDetail.objects.get(user=request.user),
                                          'public_api_key': settings.STRIPE_PUBLIC_KEY})


@login_required(login_url="/account/login")
def order_service(request):
    if request.POST:
        attach_services = AttachedService.objects.all()
        attach_services.delete()
        user_detail = UserDetail.objects.get(user=request.user)
        service = Service.objects.get(price_per_month=request.POST.get('checkout-form-service'))

        attach_service = AttachedService.objects.get_or_create(user=user_detail,
                                                        service=service,
                                                        increment=request.POST.get('checkout-form-payment-inc').lower())

    return HttpResponse('GOT IT')


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
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # add payment token to user
    try:
        stripe.Customer.modify(
            user_detail.stripe_id,
            source=request.POST.get('id')
        )
    except stripe.error.CardError:
        return HttpResponse('declined')

    attach_service = AttachedService.objects.get(user=user_detail)

    if attach_service.increment == 'yearly':
        plan = attach_service.service.yearly_id
    else:
        plan = attach_service.service.monthly_id

    # subscribe user to the selected plan
    subscription = stripe.Subscription.create(
        customer=user_detail.stripe_id,
        items=[
            {
                "plan": plan,
            },
        ]
    )

    return HttpResponse(json.dumps(subscription))