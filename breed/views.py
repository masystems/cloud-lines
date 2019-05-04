from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Breed
from .forms import BreedForm


def is_editor(user):
    return user.groups.filter(name='editor').exists() or user.is_superuser


@login_required(login_url="/account/login")
def breeds(request):
    editor = is_editor(request.user)
    breeds = Breed.objects
    return render(request, 'breeds.html', {'breeds': breeds,
                                           'editor': editor})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def new_breed_form(request):
    breed_form = BreedForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if breed_form.is_valid():
            breed_form.save()

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
    breed = Breed.objects.get(id=breed_id)
    return render(request, 'breed.html', {'breed': breed,
                                          'editor': is_editor(request.user)})