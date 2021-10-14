from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import BreedGroup
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from .forms import BreedGroupForm
from approvals.models import Approval
from json import dumps


@login_required(login_url="/account/login")
def breed_groups(request):
    attached_service = get_main_account(request.user)
    return render(request, 'breed_groups.html', {'groups': BreedGroup.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor, "/account/login")
def new_breed_group_form(request):
    breed_group_form = BreedGroupForm(request.POST or None, request.FILES or None)
    attached_service = get_main_account(request.user)
    
    # check if user has permission, passing in ids of mother and father from kinship queue item
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        # specify breeder to validate user is breeder
        if Breeder.objects.filter(account=attached_service, breeding_prefix=breed_group_form['breeder'].value()).exists():
            if not has_permission(request, {'read_only': False, 'contrib': 'breeder', 'admin': True, 'breed_admin': True},
                                            breeder_users=[Breeder.objects.get(account=attached_service, breeding_prefix=breed_group_form['breeder'].value()).user]):
                return HttpResponse(dumps({'result': 'fail', 'msg': 'You do not have permission!'}))
        # if breeder doesn't exist, allow contribs on through
        else:
            if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
                return HttpResponse(dumps({'result': 'fail', 'msg': 'You do not have permission!'}))
    else:
        raise PermissionDenied()
    
    if request.method == 'POST':
        new_breed_group = BreedGroup()
        try:
            new_breed_group.breeder = Breeder.objects.get(account=attached_service, breeding_prefix=breed_group_form['breeder'].value())
        except Breeder.DoesNotExist:
            pass
        new_breed_group.breed = Breed.objects.get(account=attached_service, breed_name=breed_group_form['breed'].value())
        new_breed_group.group_name = breed_group_form['group_name'].value()
        new_breed_group.account = attached_service
        new_breed_group.save()
        
        # variable to check that 1 male was given
        male_count = 0
        
        # add group members
        for id in breed_group_form['group_members'].value():
            # increment male_count if it's male
            if 'M | ' in id:
                male_count += 1
            
            id = id[4:]
            pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
            new_breed_group.group_members.add(pedigree)

        # check number of males given is correct
        if male_count != 1:
            return HttpResponse(dumps({'result': 'fail', 'msg': 'Number of males must be one!'}))

        if request.user in attached_service.contributors.all():
            new_breed_group.state = 'unapproved'
            new_breed_group.save()

            data = serializers.serialize('yaml', [new_breed_group])
            Approval.objects.create(account=attached_service,
                                    user=request.user,
                                    type='new',
                                    breed_group=new_breed_group,
                                    data=data)
        else:
            new_breed_group.save()

        return HttpResponse(dumps({"result": "success"}))

    else:
        breed_group_form = BreedGroupForm()

    return render(request, 'new_breed_group_form.html', {'breed_group_form': breed_group_form,
                                                         'pedigree': Pedigree.objects.filter(account=attached_service).exclude(state='unapproved'),
                                                         'breeders': Breeder.objects.filter(account=attached_service),
                                                         'breeds': Breed.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor, "/account/login")
def edit_breed_group_form(request, breed_group_id):
    breed_group = get_object_or_404(BreedGroup, id=breed_group_id)

    breed_group_form = BreedGroupForm(request.POST or None, request.FILES or None, instance=breed_group)
    attached_service = get_main_account(request.user)
    
    # check if user has permission, passing in ids of mother and father from kinship queue item
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    elif request.method == 'POST':
        # specify breeder to validate user is breeder
        if Breeder.objects.filter(account=attached_service, breeding_prefix=breed_group_form['breeder'].value()).exists():
            if not has_permission(request, {'read_only': False, 'contrib': 'breeder', 'admin': True, 'breed_admin': True},
                                            breeder_users=[Breeder.objects.get(account=attached_service, breeding_prefix=breed_group_form['breeder'].value()).user]):
                return HttpResponse(dumps({'result': 'fail', 'msg': 'You do not have permission!'}))
        # if breeder doesn't exist, allow contribs on through
        else:
            if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
                return HttpResponse(dumps({'result': 'fail', 'msg': 'You do not have permission!'}))
    else:
        raise PermissionDenied()
    
    members = []
    if request.method == 'POST':
        if request.POST.get('delete'):
            if request.user in attached_service.contributors.all():
                # contributors are not allowed to delete pedigrees!
                pass
            else:
                breed_group.delete()
                # delete any existed approvals
                approvals = Approval.objects.filter(breed_group=breed_group)
                for approval in approvals:
                    approval.delete()
            return HttpResponse(dumps({"result": "success"}))
        try:
            breed_group.breeder = Breeder.objects.get(account=attached_service, breeding_prefix=breed_group_form['breeder'].value())
        except Breeder.DoesNotExist:
            pass
        breed_group.breed = Breed.objects.get(account=attached_service, breed_name=breed_group_form['breed'].value())
        breed_group.group_name = breed_group_form['group_name'].value()

        current_members = []
        for member in breed_group.group_members.all():
            current_members.append(member)
        breed_group.group_members.clear()

        # update group members
        for id in breed_group_form['group_members'].value():
            id = id[4:]
            pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
            breed_group.group_members.add(pedigree)

        if request.user in attached_service.contributors.all():
            if not Approval.objects.filter(breed_group=breed_group).exists():
                BreedGroup.objects.filter(id=breed_group.id).update(state='edited')

                data = serializers.serialize('yaml', [breed_group, ])

                # create approval object
                Approval.objects.create(account=attached_service,
                                        user=request.user,
                                        type='edit',
                                        breed_group=breed_group,
                                        data=data)

                # reset group members
                breed_group.group_members.clear()
                for pedigree in current_members:
                    breed_group.group_members.add(pedigree)

        else:
            # update group members
            for id in breed_group_form['group_members'].value():
                id = id[4:]
                pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
                breed_group.group_members.add(pedigree)

            # delete any existed approvals
            approvals = Approval.objects.filter(breed_group=breed_group)
            for approval in approvals:
                approval.delete()
            breed_group.state = 'approved'
            breed_group.save()

        return HttpResponse(dumps({"result": "success"}))
    else:
        if breed_group.state == 'edited':
            approval = Approval.objects.get(breed_group=breed_group)
            for obj in serializers.deserialize("yaml", approval.data):
                obj.object.state = 'edited'
                breed_group = obj.object
        breed_group_form = BreedGroupForm()
        # get any existing members
        for pedigree in breed_group.group_members.all():
            members.append(pedigree.reg_no)

    return render(request, 'edit_breed_group_form.html', {'breed_group_form': breed_group_form,
                                                          'breed_group': breed_group,
                                                          'pedigree': Pedigree.objects.filter(account=attached_service).exclude(state='unapproved'),
                                                          'members': members,
                                                          'breeders': Breeder.objects.filter(account=attached_service),
                                                          'breeds': Breed.objects.filter(account=attached_service)})