from django.shortcuts import render, HttpResponse, render_to_response
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import auth
from django.db.models import Q
from .models import UserDetail, AttachedService
from .forms import InstallForm, SignUpForm
from cloud_lines.models import Service
from pedigree.models import Pedigree
from breed.models import Breed


def site_mode(request):
    if request.user.is_authenticated:
        try:
            try:
                user = UserDetail.objects.get(user=request.user)
                attached_service = AttachedService.objects.get(
                    Q(admin_users=request.user, active=True) | Q(read_only_users=request.user, active=True) | Q(
                        user=user, active=True))
            except UserDetail.DoesNotExist:
                user = False
                attached_service = AttachedService.objects.get(Q(admin_users=request.user, active=True) | Q(read_only_users=request.user, active=True))
            finally:
                service = Service.objects.get(id=attached_service.service.id)

            if user:
                if request.user == user.user:
                    editor = True
                elif request.user in attached_service.admin_users.all():
                    editor = True
                elif request.user in attached_service.read_only_users.all():
                    editor = False
                else:
                    editor = False
            else:
                editor = False

            if Pedigree.objects.filter(account=attached_service).count() < service.number_of_animals:
                pedigrees = True
            else:
                pedigrees = False

            if attached_service.admin_users.all().count() < service.admin_users:
                admins = True
            else:
                admins = False

            if attached_service.read_only_users.all().count() < service.read_only_users:
                users = True
            else:
                users = False

            if attached_service.site_mode == 'poultry' or Breed.objects.filter(account=attached_service).count() < 1:
                multi_breed = True
            else:
                multi_breed = False

            return {'service': attached_service,
                    'add_pedigree': pedigrees,
                    'admins': admins,
                    'users': users,
                    'multi_breed': multi_breed,
                    'editor': editor}

        except AttachedService.DoesNotExist:
            return {'site_mode': 'Free',
                    'animal_type': 'Pedigrees'}
        except UserDetail.DoesNotExist:
            return {'site_mode': 'Free',
                    'animal_type': 'Pedigrees'}

    return {'authenticated': 'no'}


def is_editor(user):
    try:
        user_detail = UserDetail.objects.get(user=user)
        if AttachedService.objects.get(Q(admin_users=user, active=True) | Q(read_only_users=user, active=True) | Q(user=user_detail, active=True)):
            return True
        else:
            return False
    except AttachedService.DoesNotExist:
        return False


def get_service(request):
    user_detail = UserDetail.objects.get(user=request.user)
    attached_service = AttachedService.objects.get(
        Q(admin_users=request.user, active=True) | Q(read_only_users=request.user, active=True) | Q(
            user=user_detail,
            active=True))
    return attached_service


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
    user_detail = UserDetail.objects.get(user=request.user)
    return render(request, 'profile.html', {'is_editor': is_editor(request.user),
                                            'user_detail': user_detail,})


def install(request):
    try:
        install_settings = AttachedService.objects.all().first()
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
            install_settings = AttachedService.objects.all().first()
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
        user_detail = UserDetail.objects.create(user=user,
                                            phone=request.POST.get('register-form-phone')
                                            )
        # login
        login(request, user)

        free = Service.objects.get(service_name='Free')
        attached_service = AttachedService.objects.create(animal_type='Pedigrees',
                                                          site_mode='mammal',
                                                          install_available=False,
                                                          user=user_detail,
                                                          service=free,
                                                          active=True)

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

