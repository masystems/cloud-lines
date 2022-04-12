from django.shortcuts import render, redirect, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from account.models import AttachedBolton
from .models import BirthNotification
from .forms import BirthNotificationForm
from pedigree.models import Pedigree
import re


# Create your views here.
class BirthNotificationBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)
        context['birth_notifications'] = BirthNotification.objects.filter(account=context['attached_service'])

        return context


class BnHome(BirthNotificationBase):
    template_name = 'bn_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_living = 0
        total_deceased = 0
        for bn in context['birth_notifications']:
            total_living += bn.living_males
            total_living += bn.living_females
            total_deceased += bn.deceased_males
            total_deceased += bn.deceased_females
        context['total_living'] = total_living
        context['total_deceased'] = total_deceased
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
                                                      reg_no=bn_form['mother'].value().strip())
                print('GOT IT!')
            except:
                print('Not a valid mother')

            ### father ###
            try:
                new_bn.father = Pedigree.objects.get(account=attached_service,
                                                      reg_no=bn_form['father'].value().strip())
            except:
                pass
            new_bn.user = request.user
            new_bn.account = attached_service
            new_bn.living_males = bn_form['living_males'].value().strip()
            new_bn.living_females = bn_form['living_females'].value().strip()
            new_bn.deceased_males = bn_form['deceased_males'].value().strip()
            new_bn.deceased_females = bn_form['deceased_females'].value().strip()
            new_bn.service_method = bn_form['service_method'].value().strip()
            new_bn.bn_number = bn_form['bn_number'].value().strip()
            new_bn.comments = bn_form['comments'].value().strip()
            new_bn.save()
            return redirect('bn_home')
        else:
            print(bn_form.errors)

    else:

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
                                                            'bn_number': bn_number})