from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Q
from django.core import serializers
from .models import Breeder
from pedigree.models import Pedigree
from pedigree.functions import get_site_pedigree_column_headings
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from .forms import BreederForm
import csv
import json


@login_required(login_url="/account/login")
def breeder(request, breeder_id):
    attached_service = get_main_account(request.user)
    breeder = Breeder.objects.get(account=attached_service, id=breeder_id)
    
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': True, 'contrib': True, 'admin': True, 'breed_admin': True}, breeder_users=[breeder.user]):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()

    # validate user allowed to view breeder
    if not breeder.data_visible:
        # Allow if the user is the breeder's user, an admin of the attached service, or the user of the attached service
        user_allowed = (
            request.user == breeder.user or 
            request.user in attached_service.admin_users.all() or 
            request.user == attached_service.user.user
        )

        if not user_allowed:
            raise PermissionDenied()
    
    columns, column_data = get_site_pedigree_column_headings(attached_service)
    breeder_pedigrees = Pedigree.objects.filter(account=attached_service, breeder__breeding_prefix__exact=breeder).exclude(
                state='unapproved').values('id', *columns)[:500]
    owner_pedigrees = Pedigree.objects.filter(account=attached_service,
                                                current_owner__breeding_prefix__exact=breeder).exclude(
        state='unapproved').values('id', *columns)[:500]
    
    # get custom fields
    try:
        custom_fields = json.loads(breeder.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}
    return render(request, 'breeder.html', {'breeder': breeder,
                                            'breeder_pedigrees': breeder_pedigrees,
                                            'owner_pedigrees': owner_pedigrees,
                                            'custom_fields': custom_fields,
                                            'columns': columns,
                                            'column_data': column_data
                                            })

@require_POST
@login_required(login_url="/account/login")
def update_sharing(request, id):
    # Get the 'shareData' value from the POST request
    share_data = request.POST.get('shareData') == 'true'
    attached_service = get_main_account(request.user)
    Breeder.objects.filter(account=attached_service, id=id).update(data_visible=share_data)
    return JsonResponse({'status': 'success', 'shareData': share_data})

@login_required(login_url="/account/login")
def breeders(request):
    def get_breeder_and_redirect():
        try:
            breeder = Breeder.objects.get(account=attached_service, user=request.user)
            return redirect('breeder', breeder.id)
        except Breeder.DoesNotExist:
            return render(request, 'breeders.html', {'breeders': Breeder.objects.filter(account=attached_service)})
        except:
            return render(request, 'breeders.html', {'breeders': Breeder.objects.filter(account=attached_service)})

    attached_service = get_main_account(request.user)

    if request.user in attached_service.contributors.all() or request.user in attached_service.read_only_users.all():
        return get_breeder_and_redirect()

    ## breeder data
    if request.user == attached_service.user.user or request.user in attached_service.admin_users.all():
        # editors see all
        return render(request, 'breeders.html', {'breeders': Breeder.objects.filter(account=attached_service)})
    else:
        # contrib users see themselfs and shared profiles
        # read only users see themselfs and shared profiles
        return render(request, 'breeders.html', {'breeders': Breeder.objects.filter(Q(data_visible=True) | Q(user=request.user), account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor, "/account/login")
def breeder_csv(request):
    attached_service = get_main_account(request.user)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="breeder_db.csv"'

    writer = csv.writer(response)
    writer.writerow(['breeding_prefix',
                     'contact_name',
                     'address_line_1',
                     'address_line_2',
                     'town',
                     'country',
                     'postcode',
                     'phone_number1',
                     'phone_number2',
                     'email',
                     'active'])
    breeder = Breeder.objects.filter(account=attached_service)
    for row in breeder.all():
        writer.writerow([row.breeding_prefix,
                         row.contact_name,
                         row.address_line_1,
                         row.address_line_2,
                         row.town,
                         row.country,
                         row.postcode,
                         row.phone_number1,
                         row.phone_number2,
                         row.email,
                         row.active
                         ])

    return response


@login_required(login_url="/account/login")
def new_breeder_form(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
    attached_service = get_main_account(request.user)
    breeder_form = BreederForm(request.POST or None, request.FILES or None)

    try:
        custom_fields = json.loads(attached_service.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    if request.method == 'POST':
        pre_checks = True
        if breeder_form.is_valid():
            if Breeder.objects.filter(account=attached_service, breeding_prefix=breeder_form['breeding_prefix'].value().replace("'", "").replace("/", "")).exists():
                breeder_form.add_error('breeding_prefix', 'Breeding prefix already exists')
                pre_checks = False
            if pre_checks:
                new_breeder = Breeder()
                new_breeder.breeding_prefix = breeder_form['breeding_prefix'].value().replace("'", "").replace("/", "")
                new_breeder.contact_name = breeder_form['contact_name'].value()
                new_breeder.address_line_1 = breeder_form['address_line_1'].value()
                new_breeder.address_line_2 = breeder_form['address_line_2'].value()
                new_breeder.town = breeder_form['town'].value()
                new_breeder.country = breeder_form['country'].value()
                new_breeder.postcode = breeder_form['postcode'].value()
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

                return redirect('breeder', new_breeder.id)
            else:
                # failed pre checks
                return render(request, 'new_breeder_form_base.html', {'breeder_form': breeder_form,
                                                                      'custom_fields': custom_fields})
        else:
            return render(request, 'new_breeder_form_base.html', {'breeder_form': breeder_form,
                                                                  'custom_fields': custom_fields})

    else:
        breeder_form = BreederForm()

    return render(request, 'new_breeder_form_base.html', {'breeder_form': breeder_form,
                                                          'custom_fields': custom_fields})


@login_required(login_url="/account/login")
def edit_breeder_form(request, breeder_id):
    attached_service = get_main_account(request.user)
    breeder = get_object_or_404(Breeder, id=breeder_id, account=attached_service)
    
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': 'breeder', 'admin': True, 'breed_admin': True},
                                        breeder_users=[breeder.user]):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': 'breeder', 'admin': True, 'breed_admin': True},
                                        breeder_users=[breeder.user]):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
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
            breeder = breeder_form.save()
            breeder.breeding_prefix = breeder.breeding_prefix.replace("'", "").replace("/", "")
            breeder.save()

            for id, field in custom_fields.items():
                custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])

            breeder.custom_fields = json.dumps(custom_fields)
            breeder.save()

            return redirect('breeder', breeder.id)
        else:
            return render(request, 'edit_breeder_form.html', {'breeder_form': breeder_form,
                                                              'breeder': breeder,
                                                              'custom_fields': custom_fields})

    else:
        breeder_form = BreederForm()

    return render(request, 'edit_breeder_form.html', {'breeder_form': breeder_form,
                                                      'breeder': breeder,
                                                      'custom_fields': custom_fields})


@csrf_exempt
def breeder_check(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        breeding_prefix = request.POST.get('breeding_prefix')
        return HttpResponse(Breeder.objects.filter(account=attached_service, breeding_prefix=breeding_prefix).exists())


@login_required(login_url="/account/login")
@user_passes_test(is_editor, "/account/login")
@never_cache
def get_breeder_details(request):
    attached_service = get_main_account(request.user)
    
    # get the pedigree that was input
    try:
        breeder = Breeder.objects.get(account=attached_service, breeding_prefix=request.GET['id'])
    except Breeder.DoesNotExist:
        return HttpResponse(json.dumps({'result': 'fail'}))
    except MultiValueDictKeyError:
        return HttpResponse(json.dumps({'result': 'fail'}))

    # if the input field required breeder to be free, return fail if the input breeder is not free
    if request.GET.get('type'):
        if (request.GET['type'] == 'free' and breeder.user):
            return HttpResponse(json.dumps({'result': 'fail'}))
    
    breeder = serializers.serialize('json', [breeder], ensure_ascii=False)
    return HttpResponse(json.dumps({'result': 'success',
                                    'breeder': breeder}))