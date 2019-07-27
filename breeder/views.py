from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Breeder
from pedigree.models import Pedigree
from breed_group.models import BreedGroup
from account.views import is_editor, get_main_account
from .forms import BreederForm
import csv
import json


@login_required(login_url="/account/login")
def breeder(request, breeder):
    attached_service = get_main_account(request.user)
    breeder = Breeder.objects.get(account=attached_service, breeding_prefix=breeder)
    pedigrees = Pedigree.objects.filter(account=attached_service, breeder__breeding_prefix__exact=breeder)
    owned = Pedigree.objects.filter(account=attached_service, current_owner__breeding_prefix__exact=breeder)
    groups = BreedGroup.objects.filter(breeder=breeder)
    # get custom fields
    try:
        custom_fields = json.loads(breeder.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}
    return render(request, 'breeder.html', {'breeder': breeder,
                                            'pedigrees': pedigrees,
                                            'owned': owned,
                                            'groups': groups,
                                            'custom_fields': custom_fields})


@login_required(login_url="/account/login")
def breeders(request):
    attached_service = get_main_account(request.user)
    breeders = Breeder.objects.filter(account=attached_service)
    return render(request, 'breeders.html', {'breeders': breeders})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def breeder_csv(request):
    attached_service = get_main_account(request.user)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="breeder_db.csv"'

    writer = csv.writer(response)
    writer.writerow(['breeding_prefix',
                     'contact_name',
                     'address',
                     'phone_number1',
                     'phone_number2',
                     'email',
                     'active'])
    breeder = Breeder.objects.filter(account=attached_service)
    for row in breeder.all():
        writer.writerow([row.breeding_prefix,
                         row.contact_name,
                         row.address,
                         row.phone_number1,
                         row.phone_number2,
                         row.email,
                         row.active
                         ])

    return response


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def new_breeder_form(request):
    attached_service = get_main_account(request.user)
    breeder_form = BreederForm(request.POST or None, request.FILES or None)

    try:
        custom_fields = json.loads(attached_service.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    if request.method == 'POST':
        if breeder_form.is_valid():
            new_breeder = Breeder()
            new_breeder.breeding_prefix = breeder_form['breeding_prefix'].value()
            new_breeder.contact_name = breeder_form['contact_name'].value()
            new_breeder.address = breeder_form['address'].value()
            new_breeder.phone_number1 = breeder_form['phone_number1'].value()
            new_breeder.phone_number2 = breeder_form['phone_number2'].value()
            new_breeder.email = breeder_form['email'].value()
            new_breeder.active = breeder_form['active'].value()
            new_breeder.account = attached_service

            try:
                custom_fields = json.loads(attached_service.custom_fields)

                for id, field in custom_fields.items():
                    custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])
            except json.decoder.JSONDecodeError:
                pass

            new_breeder.custom_fields = json.dumps(custom_fields)
            new_breeder.save()

            return redirect('breeder', new_breeder.breeding_prefix)
        else:
            print(request.POST)

    else:
        breeder_form = BreederForm()

    return render(request, 'new_breeder_form_base.html', {'breeder_form': breeder_form,
                                                          'custom_fields': custom_fields})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def edit_breeder_form(request, breeder_id):
    attached_service = get_main_account(request.user)
    breeder = get_object_or_404(Breeder, id=breeder_id, account=attached_service)
    breeder_form = BreederForm(request.POST or None, request.FILES or None, instance=breeder)

    try:
        # get custom fields
        custom_fields = json.loads(breeder.custom_fields)
    except json.decoder.JSONDecodeError:
        try:
            # get custom fields template
            custom_fields = json.loads(attached_service.custom_fields)
        except json.decoder.JSONDecodeError:
            custom_fields = {}

    if request.method == 'POST':
        if 'delete' in request.POST:
            breeder.delete()
            return redirect('breeders')
        if breeder_form.is_valid():
            breeder_form.save()

            for id, field in custom_fields.items():
                custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])

            breeder.custom_fields = json.dumps(custom_fields)
            breeder.save()

            return redirect('breeder', breeder.breeding_prefix)

    else:
        breeder_form = BreederForm()

    return render(request, 'edit_breeder_form.html', {'breeder_form': breeder_form,
                                                      'breeder': breeder,
                                                      'custom_fields': custom_fields})


@csrf_exempt
def breeder_check(request):
    if request.method == 'POST':
        breeding_prefix = request.POST.get('breeding_prefix')
        return HttpResponse(Breeder.objects.filter(breeding_prefix=breeding_prefix).exists())