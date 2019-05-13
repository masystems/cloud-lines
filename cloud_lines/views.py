from django.shortcuts import render, HttpResponse, redirect
from .models import Service, Page, Faq, Contact
from django.core.mail import EmailMessage, BadHeaderError
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


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email_address = request.POST.get('email')
        phone = request.POST.get('phone')
        service = request.POST.get('service')
        subject = request.POST.get('subject')
        message_body = request.POST.get('message')
        email = EmailMessage(
            subject,
            "From: {},\nPhone: {},\nService: {},\nMessage: {}".format(name,
                                                                      phone,
                                                                      service,
                                                                      message_body),
            'contact@cmdlb.com',
            ['marco@masys.co.uk', 'adam@masys.co.uk'],
            reply_to=[email_address],
        )
        try:
            email.send(fail_silently=False)
            email_obj = Contact.objects.create(name=name,
                                               email=email_address,
                                               phone=phone,
                                               service=service,
                                               subject=subject,
                                               message=message_body)
            email_obj.save()
        except:
            redirect('result', 'fail')

        return redirect('result', 'success')
    else:
        return render(request, 'contact.html', {'services': Service.objects.all()})


def result(request, result):
    content = {}
    if result == 'success':
        content['title'] = 'Success'
        content['sub_title'] = 'Message received!'
        content['body'] = """<h4>Got it!</h4>
                                <div class="style-msg successmsg">
                                <div class="sb-msg"><i class="icon-thumbs-up"></i><strong>Received!</strong> You successfully sent us a message and we'll get back to you ASAP.</div>
                                <button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>
                            </div>"""
    elif result == 'fail':
        content['title'] = 'Oops'
        content['sub_title'] = 'Something went wrong!'
        content['body'] = """<h4>Oh no!</h4>
                                <div class="style-msg errormsg">
                                <div class="sb-msg"><i class="icon-remove"></i><strong>Oh snap!</strong> We're working on it!</div>
                            </div>"""
    return render(request, 'std_page.html', {'content': content,
                                             'services': Service.objects.all()})
