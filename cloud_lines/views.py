from django.shortcuts import render, HttpResponse, redirect
from .models import Service, Page, Faq
from django.core.mail import send_mail, BadHeaderError
from .forms import ContactForm

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
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            subject = form.cleaned_data['subject']
            service = form.cleaned_data['service']
            message = form.cleaned_data['message']
            try:
                send_mail(subject, message, email, ['marco@masys.co.uk'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('success')
    return render(request, 'contact.html', {'services': Service.objects.all()})

def successView(request):
    return HttpResponse('Success! Thank you for your message.')