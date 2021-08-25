from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from account.views import is_editor, get_main_account, send_mail, has_permission, redirect_2_login
from .models import Approval
from pedigree.models import Pedigree, PedigreeImage
from breed_group.models import BreedGroup
from breeder.models import Breeder
from breed.models import Breed
from yaml import load
from json import loads


@login_required(login_url="/account/login")
def approvals(request):
    # check if user has permission (breeds admins allowed to page, but blocked from doing things with approvals they're not admin for)
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}, []):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()
    
    attached_service = get_main_account(request.user)
    approvals = Approval.objects.filter(account=attached_service)
    data = []

    for approval in approvals:
        if approval.pedigree:
            for obj in serializers.deserialize("yaml", approval.data):
                if obj.object.custom_fields != '':
                    obj.object.custom_fields_expanded = loads(obj.object.custom_fields)
                else:
                    obj.object.custom_fields_expanded = "{}"
                data.append(obj.object)
        elif approval.breed_group:
            # convert the data to a dict
            data_dict = load(approval.data)[0]
            # get the breeder
            try:
                breeder = Breeder.objects.get(id=data_dict['fields']['breeder'])
                data_dict['fields']['breeder'] = breeder.breeding_prefix
            except ObjectDoesNotExist:
                data_dict['fields']['breeder'] = None
            # get the breed
            breed = Breed.objects.get(id=data_dict['fields']['breed'])
            data_dict['fields']['breed'] = breed.breed_name
            # get pedigrees
            pedigrees = []
            for pedigree in data_dict['fields']['group_members']:
                pedigrees.append(Pedigree.objects.get(id=pedigree))
            data_dict['fields']['group_members'] = pedigrees
            data.append(data_dict)
    return render(request, 'approvals.html', {'approvals': approvals,
                                              'data': data})


@login_required(login_url="/account/login")
def approve(request, id):
    approval = Approval.objects.get(id=id)
    
    # check if user has permission (should just be a GET)
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': 'breed'}, [approval.pedigree]):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()
    
    for obj in serializers.deserialize("yaml", approval.data):
        obj.object.state = 'approved'
        obj.object.save()

    if approval.pedigree:
        data_dict = load(approval.data)[0]
        try:
            approval.pedigree.parent_mother = Pedigree.objects.get(id=str(data_dict['fields']['parent_mother']))
        except ValueError:
            pass
        try:
            approval.pedigree.parent_father = Pedigree.objects.get(id=str(data_dict['fields']['parent_father']))
        except ValueError:
            pass

        # approve images
        images = PedigreeImage.objects.filter(reg_no=approval.pedigree)
        for image in images:
            image.state = 'approved'
            image.save()

    elif approval.breed_group:
        data_dict = load(approval.data)[0]
        approval.breed_group.group_members.clear()
        for pedigree in data_dict['fields']['group_members']:
            approval.breed_group.group_members.add(Pedigree.objects.get(id=pedigree))

    approval.delete()

    return redirect('approvals')


@login_required(login_url="/account/login")
def declined(request):
    approval = ''
    # check if user has permission
    if request.method == 'GET':
        return redirect_2_login(request)
    elif request.method == 'POST':
        approval = Approval.objects.get(id=request.POST.get('decline-id'))
        # particular breed checked below
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': 'breed'}, [approval.pedigree]):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

    if request.method == 'POST':
        if approval.pedigree:
            message_approval_id = approval.pedigree.reg_no
            if approval.type == 'new':
                # delete new entry
                approval.pedigree.delete()
            else:
                # mark edited items as approved but do not save yaml data from approval object
                Pedigree.objects.filter(id=approval.pedigree.id).update(state='approved')

            # un-approve images
            images = PedigreeImage.objects.filter(reg_no=approval.pedigree)
            for image in images:
                image.delete()

        elif approval.breed_group:
            message_approval_id = approval.breed_group.group_name
            if approval.type == 'new':
                # delete new entry
                approval.breed_group.delete()
            else:
                # mark edited items as approved but do not save yaml data from approval object
                BreedGroup.objects.filter(id=approval.breed_group.id).update(state='approved')
        approval.delete()

        message = """{} has decline your change approval request for {} with the following message:
        
        {}
        """.format(request.user.get_full_name(), message_approval_id, request.POST.get('message'))

        send_mail('Cloud-Lines approval declined for {}'.format(message_approval_id), approval.user.get_full_name(), message,
                  send_to=approval.user.email,
                  send_from='contact@masys.co.uk',
                  reply_to=request.user.email)

    return redirect('approvals')