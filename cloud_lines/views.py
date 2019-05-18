from django.shortcuts import render, redirect, HttpResponse
from .models import Service, Page, Faq, Contact
from django.core.mail import EmailMessage
import json

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