from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Breed
from .forms import BreedForm
from account.models import SiteDetail


def is_editor(user):
    try:
        if SiteDetail.objects.get(admin_users=user) or user.is_superuser:
            return True
        else:
            return False
    except SiteDetail.DoesNotExist:
        return False


@login_required(login_url="/account/login")
def breeds(request):
    editor = is_editor(request.user)
    site_detail = SiteDetail.objects.get(Q(admin_users=request.user) | Q(read_only_users=request.user))
    breeds = Breed.objects.filter(account=site_detail)
    return render(request, 'breeds.html', {'breeds': breeds,
                                           'editor': editor})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def new_breed_form(request):
    breed_form = BreedForm(request.POST or None, request.FILES or None)
    site_detail = SiteDetail.objects.get(Q(admin_users=request.user) | Q(read_only_users=request.user))

    if request.method == 'POST':
        if breed_form.is_valid():
            breed = breed_form.save()
            Breed.objects.filter(id=breed.id).update(account=site_detail)
            return redirect('breeds')

    else:
        breed_form = BreedForm()

    return render(request, 'new_breed_form.html', {'breed_form': breed_form})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def edit_breed_form(request, breed_id):
    breed = get_object_or_404(Breed, id=breed_id)
    breed_form = BreedForm(request.POST or None, request.FILES or None, instance=breed)

    if request.method == 'POST':
        if 'delete' in request.POST:
            breed.delete()
            return redirect('breeds')

        if breed_form.is_valid():
            breed_form.save()
            return redirect('breeds')

    else:
        breed_form = BreedForm()

    return render(request, 'edit_breed_form.html', {'breed_form': breed_form,
                                                    'breed': breed})


@login_required(login_url="/account/login")
def view_breed(request, breed_id):
    site_detail = SiteDetail.objects.get(Q(admin_users=request.user) | Q(read_only_users=request.user))
    breed = Breed.objects.get(account=site_detail, id=breed_id)
    return render(request, 'breed.html', {'breed': breed,
                                          'editor': is_editor(request.user)})