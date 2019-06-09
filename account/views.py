from django.shortcuts import render, HttpResponse, render_to_response
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .models import SiteDetail, SignUpForm, UserDetail
from .forms import InstallForm
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import auth
import json


def site_mode(request):
    try:
        site_details = SiteDetail.objects.all().first()
        return {'site_mode': site_details.site_mode,
                'animal_type': site_details.animal_type}
    except:
        return {'site_mode': None,
                'animal_type': 'Pedigrees'}


def is_editor(user):
    return {'is_editor': user.groups.filter(name='editor').exists() or user.is_superuser}


@login_required(login_url="/account/login")
def new_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})


def site_login(request):
    if request.method == 'POST':
        user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            auth.login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Username or Password does not exist.'})
    else:
        return render(request, 'login.html')


@login_required(login_url="/account/login")
def logout(request):
    # TO DO neet to go to homepage and logout
    # if request.method == 'POST':
    auth.logout(request)
    return redirect('home')


@login_required(login_url="/account/login")
def profile(request):
    return render(request, 'profile.html', {'is_editor': is_editor(request.user)})


def install(request):
    try:
        install_settings = SiteDetail.objects.all().first()
        install_form = InstallForm(request.POST or None, request.FILES or None, instance=install_settings)
    except:
        install_form = InstallForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if install_form.is_valid():
            username = install_form.data['username']
            raw_password = install_form.data['password']
            email = install_form.data['email']
            user = User.objects.create_user(username=username,
                                            email=email,
                                            password=raw_password,
                                            first_name=install_form.data['firstname'],
                                            last_name=install_form.data['lastname'])
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            install_form.save()
            install_settings = SiteDetail.objects.all().first()
            install_settings.install_available = False
            install_settings.save()

            return redirect('home')
    else:
        install_form = InstallForm()

    return render(request, 'install.html', {'install_form': install_form})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('register-form-username')
        raw_password = request.POST.get('register-form-password')
        email = request.POST.get('register-form-email')
        User.objects.create_user(username=username,
                                 email=email,
                                 password=raw_password,
                                 first_name=request.POST.get('register-form-first-name'),
                                 last_name=request.POST.get('register-form-last-name'))
        user = authenticate(username=username, password=raw_password)

        # update user details
        details = UserDetail.objects.create(user=user,
                                            phone=request.POST.get('register-form-phone')
                                            )

        login(request, user)
        return redirect('order')
    else:
        return render(request, 'login.html')


def username_check(request):
    if request.method == 'POST':
        username = request.POST.get('register-form-username')
        return HttpResponse(User.objects.filter(username=username).exists())


def email_check(request):
    if request.method == 'POST':
        email = request.POST.get('register-form-email')
        return HttpResponse(User.objects.filter(email=email).exists())

