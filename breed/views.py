from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Breed
from .forms import BreedForm
from account.views import is_editor, get_main_account


@login_required(login_url="/account/login")
def breeds(request):
    attached_service = get_main_account(request.user)
    breeds = Breed.objects.filter(account=attached_service)
    if len(breeds) == 1:
        return redirect('view_breed', breeds[0].id)
    else:
        return render(request, 'breeds.html', {'breeds': breeds,})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def new_breed_form(request):
    breed_form = BreedForm(request.POST or None, request.FILES or None)
    attached_service = get_main_account(request.user)

    if request.method == 'POST':
        if breed_form.is_valid():
            breed = breed_form.save()
            Breed.objects.filter(id=breed.id).update(account=attached_service)
            return redirect('breeds')

    else:
        breed_form = BreedForm()

    return render(request, 'new_breed_form_base.html', {'breed_form': breed_form})


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
    attached_service = get_main_account(request.user)
    breed = Breed.objects.get(account=attached_service, id=breed_id)
    return render(request, 'breed.html', {'breed': breed,
                                          'editor': is_editor(request.user)})