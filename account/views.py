from django.shortcuts import render, HttpResponse, render_to_response
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import auth
from django.db.models import Q
from .models import UserDetail, AttachedService
from .forms import InstallForm, SignUpForm
from cloud_lines.models import Service
from pedigree.models import Pedigree
from breed.models import Breed
import random
import string


def site_mode(request):

    if request.user.is_authenticated:
        # returns the main account the requesting user is a member of
        main_account = get_main_account(request.user)

        # returns the user for the main account
        user = UserDetail.objects.get(user=main_account.user.user)

        attached_services = AttachedService.objects.filter(Q(admin_users=request.user) | Q(read_only_users=request.user) | Q(user=user))

        service = Service.objects.get(id=main_account.service.id)

        if str(request.user.username) == str(user.user.username):

            editor = True
        elif request.user in main_account.admin_users.all():
            editor = True
        elif request.user in main_account.read_only_users.all():
            editor = False
        else:
            editor = False

        if Pedigree.objects.filter(account=main_account).count() < service.number_of_animals:
            pedigrees = True
        else:
            pedigrees = False

        if main_account.admin_users.all().count() < service.admin_users:
            admins = True
        else:
            admins = False

        if main_account.read_only_users.all().count() < service.read_only_users:
            users = True
        else:
            users = False

        if main_account.site_mode == 'poultry' or Breed.objects.filter(account=main_account).count() < 1:
            multi_breed = True
        else:
            multi_breed = False

        return {'service': main_account,
                'attached_services': attached_services,
                'add_pedigree': pedigrees,
                'admins': admins,
                'users': users,
                'multi_breed': multi_breed,
                'editor': editor}

    return {'authenticated': 'no'}


def is_editor(user):
    try:
        main_account = get_main_account(user)
        if user in main_account.admin_users.all():
            return True
        elif user == main_account.user.user:
            return True
        else:
            return False
    except UserDetail.DoesNotExist:
        return False
    except AttachedService.DoesNotExist:
        return False


def get_main_account(user):
    # get detail for logged in user
    user_detail = UserDetail.objects.get(user=user)
    try:
        # get the attached service of the logged in user
        try:
            user_service = AttachedService.objects.get(admin_users=user, active=True)
        except AttachedService.DoesNotExist:
            try:
                user_service = AttachedService.objects.get(read_only_users=user, active=True)
            except AttachedService.DoesNotExist:
                try:
                    user_service = AttachedService.objects.get(user=user_detail, active=True)
                except AttachedService.DoesNotExist:
                    pass

        # get attached service of the primary user
        attached_service = AttachedService.objects.get(user=user_service.user, active=True)
    except AttachedService.DoesNotExist:
        # update the attached service to what default
        attached_service = AttachedService.objects.filter(user=user_detail).update(animal_type='Pedigrees',
                                                                               site_mode='mammal',
                                                                               install_available=False,
                                                                               service=Service.objects.get(service_name='Free'),
                                                                               active=True)

    return attached_service


@login_required(login_url="/account/login")
def user_edit(request):
    if request.method == 'POST':
        main_account = get_main_account(request.user)

        if request.POST.get('formType') == 'new':
            # generate password
            password = ''.join(
                [random.choice(string.ascii_letters + string.digits + string.punctuation) for n in range(int(10))])

            # create new user
            user = User.objects.create_user(username=request.POST.get('register-form-username').lower(),
                                            email=request.POST.get('register-form-email'),
                                            password=password,
                                            first_name=request.POST.get('firstName'),
                                            last_name=request.POST.get('lastName'))

            # update user details
            user_detail = UserDetail.objects.create(user=user,
                                                    phone=''
                                                    )
            user_service = AttachedService.objects.filter(user=user_detail).update(animal_type='Pedigrees',
                                                                                   install_available=False,
                                                                                   active=False)

            if request.POST.get('status') == 'Editor':
                main_account.admin_users.add(user)
            else:
                main_account.read_only_users.add(user)

            return HttpResponse(True)
        elif request.POST.get('formType') == 'edit':
            # find user and update name fields
            User.objects.filter(username=request.POST.get('register-form-username'),
                                email=request.POST.get('register-form-email')).update(first_name=request.POST.get('firstName'),
                                                                                      last_name=request.POST.get('lastName'))
            user = User.objects.get(username=request.POST.get('register-form-username'),
                                    email=request.POST.get('register-form-email'))
            # remove user from admins and read only users
            main_account.admin_users.remove(user)
            main_account.read_only_users.remove(user)

            # add user to the request group
            if request.POST.get('status') == 'Editor':
                main_account.admin_users.add(user)
            else:
                main_account.read_only_users.add(user)

            return HttpResponse(True)
        elif request.POST.get('formType') == 'delete':
            print('deleting user!')
            User.objects.get(username=request.POST.get('register-form-username'),
                             email=request.POST.get('register-form-email')).delete()
            return HttpResponse(True)


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
    main_account = get_main_account(request.user)

    if str(request.user) == str(main_account.user):
        services = Service.objects.all().exclude(service_name='Free')
        recommended = Service.objects.filter(id=user_detail.attached_service.service.id+1)
    else:
        services = None
        recommended = None
    return render(request, 'profile.html', {'user_detail': user_detail,
                                            'services': services,
                                            'recommended': recommended})


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


@csrf_exempt
def username_check(request):
    if request.method == 'POST':
        username = request.POST.get('register-form-username')
        return HttpResponse(User.objects.filter(username=username).exists())


@csrf_exempt
def email_check(request):
    if request.method == 'POST':
        email = request.POST.get('register-form-email')
        return HttpResponse(User.objects.filter(email=email).exists())

