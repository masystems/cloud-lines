from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from account.views import is_editor, get_main_account
from .models import Approval
from pedigree.models import Pedigree
from breed_group.models import BreedGroup
from json import loads

@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def approvals(request):
    attached_service = get_main_account(request.user)
    approvals = Approval.objects.filter(account=attached_service)
    data = []
    for approval in approvals:
        for obj in serializers.deserialize("yaml", approval.data):
            data.append(obj.object)
    return render(request, 'approvals.html', {'approvals': approvals,
                                              'data': data})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def approve(request, id):
    approval = Approval.objects.get(id=id)
    for obj in serializers.deserialize("yaml", approval.data):
        obj.object.state = 'approved'
        obj.object.save()
    approval.approved = True
    approval.save()

    return redirect('approvals')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def declined(request, id):
    approval = Approval.objects.get(id=id)
    if approval.pedigree:
        Pedigree.objects.filter(id=approval.pedigree.id).update(state='approved')
    elif approval.breed_group:
        BreedGroup.objects.filter(id=approval.breed_group.id).update(state='approved')

    approval.approved = False
    approval.save()
    return redirect('approvals')