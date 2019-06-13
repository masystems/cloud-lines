from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import BreedGroup
from pedigree.models import Pedigree
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_service
from .forms import BreedGroupForm


@login_required(login_url="/account/login")
def breed_groups(request):
    attached_service = get_service(request)
    return render(request, 'breed_groups.html', {'groups': BreedGroup.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def new_breed_group_form(request):
    breed_group_form = BreedGroupForm(request.POST or None, request.FILES or None)
    attached_service = get_service(request)
    if request.method == 'POST':
        new_breed_group = BreedGroup()
        new_breed_group.breeder = Breeder.objects.get(prefix=breed_group_form['breeder'].value())
        new_breed_group.breed = Breed.objects.get(breed_name=breed_group_form['breed'].value())
        new_breed_group.group_name = breed_group_form['group_name'].value()
        group = new_breed_group.save()
        BreedGroup.objects.filter(id=group.id).update(account=attached_service)
        # add group members
        for id in breed_group_form['group_members'].value():
            id = id[4:]
            pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
            new_breed_group.group_members.add(pedigree)
        new_breed_group.save()

        return redirect('breed_groups')

    else:
        breed_group_form = BreedGroupForm()

    return render(request, 'new_breed_group_form.html', {'breed_group_form': breed_group_form,
                                                         'pedigree': Pedigree.objects.filter(account=attached_service),
                                                         'breeders': Breeder.objects.filter(account=attached_service),
                                                         'breeds': Breed.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def edit_breed_group_form(request, breed_group_id):
    breed_group = get_object_or_404(BreedGroup, id=breed_group_id)
    breed_group_form = BreedGroupForm(request.POST or None, request.FILES or None, instance=breed_group)
    attached_service = get_service(request)
    members = []
    if request.method == 'POST':
        if 'delete' in request.POST:
            breed_group.delete()
            return redirect('breed_groups')
        breed_group.breeder = Breeder.objects.get(prefix=breed_group_form['breeder'].value())
        breed_group.breed = Breed.objects.get(breed_name=breed_group_form['breed'].value())
        breed_group.group_name = breed_group_form['group_name'].value()
        # clear existing members
        breed_group.group_members.clear()
        # update group members
        for id in breed_group_form['group_members'].value():
            id = id[4:]
            pedigree = Pedigree.objects.get(account=attached_service, reg_no=id)
            breed_group.group_members.add(pedigree)
        breed_group.save()

        return redirect('breed_groups')
    else:
        breed_group_form = BreedGroupForm()
        # get any existing members
        for pedigree in breed_group.group_members.all():
            members.append(pedigree.reg_no)

    return render(request, 'edit_breed_group_form.html', {'breed_group_form': breed_group_form,
                                                          'breed_group': breed_group,
                                                          'pedigree': Pedigree.objects.filter(account=attached_service),
                                                          'members': members,
                                                          'breeders': Breeder.objects.filter(account=attached_service),
                                                          'breeds': Breed.objects.filter(account=attached_service)})