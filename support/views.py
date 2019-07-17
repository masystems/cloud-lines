from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SupportForm
from .models import Ticket
from account.views import send_mail
from account.views import is_editor, get_main_account


@login_required(login_url="/account/login")
def support(request):
    support_form = SupportForm(request.POST or None, request.FILES or None)
    attached_service = get_main_account(request.user)

    if request.method == 'POST':
        if support_form.is_valid():
            support = support_form.save()
            Ticket.objects.filter(id=support.id).update(account=attached_service, user=request.user)
            body = """
                Priority: {},
                Subject: {},
                Description: {},
            """.format(request.user, request.POST.get('priority'), request.POST.get('subject'), request.POST.get('description'))
            send_mail('Support Request', request.user, body, reply_to=request.user.email)

            return redirect('support')

    else:
        support_form = SupportForm()

    return render(request, 'support.html', {'support_form': support_form,
                                            'tickets': Ticket.objects.filter(account=attached_service).order_by('-date_time')})


@login_required(login_url="/account/login")
def faq(request):
    return render(request, 'faq.html')