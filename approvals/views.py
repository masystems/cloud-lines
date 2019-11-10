from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from account.views import is_editor, get_main_account
from .models import Approval
from pedigree.models import Pedigree
from breed_group.models import BreedGroup
from breeder.models import Breeder
from breed.models import Breed
from yaml import load
from json import loads


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def approvals(request):
    attached_service = get_main_account(request.user)
    approvals = Approval.objects.filter(account=attached_service)
    data = []

    for approval in approvals:
        if approval.pedigree:
            for obj in serializers.deserialize("yaml", approval.data):
                obj.object.custom_fields_expanded = loads(obj.object.custom_fields)
                data.append(obj.object)
        elif approval.breed_group:
            # convert the data to a dict
            data_dict = load(approval.data)[0]
            # get the breeder
            breeder = Breeder.objects.get(id=data_dict['fields']['breeder'])
            data_dict['fields']['breeder'] = breeder.breeding_prefix
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
@user_passes_test(is_editor)
def approve(request, id):
    approval = Approval.objects.get(id=id)
    for obj in serializers.deserialize("yaml", approval.data):
        obj.object.state = 'approved'
        obj.object.save()

    if approval.pedigree:
        data_dict = load(approval.data)[0]
        print(str(data_dict['fields']['parent_father']))
        try:
            approval.pedigree.parent_mother = Pedigree.objects.get(id=str(data_dict['fields']['parent_mother']))
        except ValueError:
            pass
        try:
            approval.pedigree.parent_father = Pedigree.objects.get(id=str(data_dict['fields']['parent_father']))
        except ValueError:
            pass
    elif approval.breed_group:
        data_dict = load(approval.data)[0]
        approval.breed_group.group_members.clear()
        for pedigree in data_dict['fields']['group_members']:
            approval.breed_group.group_members.add(Pedigree.objects.get(id=pedigree))

    approval.delete()

    return redirect('approvals')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def declined(request, id):
    approval = Approval.objects.get(id=id)
    if approval.pedigree:
        if approval.type == 'new':
            # delete new entry
            approval.pedigree.delete()
        else:
            # mark edited items as approved but do not save yaml data from approval object
            Pedigree.objects.filter(id=approval.pedigree.id).update(state='approved')
    elif approval.breed_group:
        if approval.type == 'new':
            # delete new entry
            approval.breed_group.delete()
        else:
            # mark edited items as approved but do not save yaml data from approval object
            BreedGroup.objects.filter(id=approval.breed_group.id).update(state='approved')
    approval.delete()

    return redirect('approvals')