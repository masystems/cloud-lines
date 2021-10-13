from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from .models import BreedGroup
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_main_account
from .forms import BreedGroupForm
from approvals.models import Approval


@login_required(login_url="/account/login")
def breed_groups(request):
    attached_service = get_main_account(request.user)
    return render(request, 'breed_groups.html', {'groups': BreedGroup.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor, "/account/login")
def new_breed_group_form(request):
    breed_group_form = BreedGroupForm(request.POST or None, request.FILES or None)
    attached_service = get_main_account(request.user)
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
        # add group members
        for id in breed_group_form['group_members'].value():
            print('M | ' in id)
            id = id[4:]
            pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
            new_breed_group.group_members.add(pedigree)

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

        return redirect('breed_groups')

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
    members = []
    if request.method == 'POST':
        if 'delete' in request.POST:
            if request.user in attached_service.contributors.all():
                # contributors are not allowed to delete pedigrees!
                pass
            else:
                breed_group.delete()
                # delete any existed approvals
                approvals = Approval.objects.filter(breed_group=breed_group)
                for approval in approvals:
                    approval.delete()
            return redirect('breed_groups')
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

        return redirect('breed_groups')
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