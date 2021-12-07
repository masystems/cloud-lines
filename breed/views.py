from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.models import User
from .models import Breed
from .forms import BreedForm
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
import json


@login_required(login_url="/account/login")
def breeds(request):
    attached_service = get_main_account(request.user)
    breeds = Breed.objects.filter(account=attached_service)
    if len(breeds) == 1:
        return redirect('view_breed', breeds[0].id)
    else:
        return render(request, 'breeds.html', {'breeds': breeds,})


@login_required(login_url="/account/login")
def new_breed_form(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
    breed_form = BreedForm(request.POST or None, request.FILES or None)
    attached_service = get_main_account(request.user)

    try:
        custom_fields = json.loads(attached_service.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    if request.method == 'POST':
        if breed_form.is_valid():
            if isinstance(breed_form['mk_threshold'].value(), float):
                mk = breed_form['mk_threshold'].value()
            else:
                mk = 0.0000

            breed = Breed.objects.create(account=attached_service,
                                         breed_name=breed_form['breed_name'].value(),
                                         breed_description=breed_form['breed_description'].value(),
                                         mk_threshold=mk)
            breed.save()
            try:
                breed.image = request.FILES['image']
            except MultiValueDictKeyError:
                pass

            try:
                custom_fields = json.loads(attached_service.custom_fields)

                for id, field in custom_fields.items():
                    custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])
            except json.decoder.JSONDecodeError:
                pass

            breed.custom_fields = json.dumps(custom_fields)
            breed.save()
            return redirect('breeds')

    else:
        breed_form = BreedForm()

    return render(request, 'new_breed_form_base.html', {'breed_form': breed_form,
                                                        'custom_fields': custom_fields})


@login_required(login_url="/account/login")
def edit_breed_form(request, breed_id):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': False}):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
    breed = get_object_or_404(Breed, id=breed_id)
    attached_service = get_main_account(request.user)
    breed_form = BreedForm(request.POST or None, request.FILES or None, instance=breed)

    try:
        # get custom fields
        custom_fields = json.loads(breed.custom_fields)
    except json.decoder.JSONDecodeError:
        try:
            # get custom fields template
            custom_fields = json.loads(attached_service.custom_fields)
        except json.decoder.JSONDecodeError:
            custom_fields = {}

    if request.method == 'POST':
        if 'delete' in request.POST:
            breed.delete()
            return redirect('breeds')

        if breed_form.is_valid():
            breed_form.save()

            for id, field in custom_fields.items():
                custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])

            breed.custom_fields = json.dumps(custom_fields)
            breed.save()

            # flush breed admins
            breed.breed_admins.clear()
            # go through the input breed admins
            breed_admin_index = 0
            while request.POST.get(f'breed_admin-{breed_admin_index}'):
                username = request.POST.get(f'breed_admin-{breed_admin_index}')
                # try to add each breed admin to breed
                try:
                    breed.breed_admins.add(User.objects.get(username=username))
                except User.DoesNotExist:
                    return HttpResponse(json.dumps({"result": "fail", "msg": f"{username} is not a user!"}))
                breed_admin_index += 1
            breed.save()

            return HttpResponse(json.dumps({"result": "success"}))
        else:
            print('tits')

    else:
        breed_form = BreedForm()

    return render(request, 'edit_breed_form.html', {'breed_form': breed_form,
                                                    'breed': breed,
                                                    'custom_fields': custom_fields})


@login_required(login_url="/account/login")
def view_breed(request, breed_id):
    attached_service = get_main_account(request.user)
    breed = Breed.objects.get(account=attached_service, id=breed_id)

    # get custom fields
    try:
        custom_fields = json.loads(breed.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    return render(request, 'breed.html', {'breed': breed,
                                          'custom_fields': custom_fields})