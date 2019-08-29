from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from pedigree.models import Pedigree, PedigreeAttributes, PedigreeImage
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_main_account
from .models import DatabaseUpload
from datetime import datetime
from os.path import splitext
import csv


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def export(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        fields = request.POST.getlist('fields')
        date = datetime.now()
        if request.POST['submit'] == 'xlsx':
            pass
        elif request.POST['submit'] == 'csv':
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="pedigree_db{}.csv"'.format(date.strftime("%Y-%m-%d"))

            writer = csv.writer(response)
            header = False

            for pedigree in Pedigree.objects.filter(account=attached_service):
                head = ''
                row = ''
                for key, val in pedigree.__dict__.items():
                    if not header:
                        if key != '_state':
                            head += '{},'.format(key)
                    if key in fields:
                        row += '{},'.format(val)
                if not header:
                    writer.writerow([head])
                    header = True
                writer.writerow([row])

            return response
        elif request.POST['submit'] == 'pdf':
            pass

    return render(request, 'export.html', {'fields': Pedigree._meta.get_fields(include_parents=False, include_hidden=False)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def importx(request):
    allowed_file_types = ('.csv')
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        database_file = request.FILES['uploadDatabase']
        imported_headings = []

        f_type = splitext(str(request.FILES['uploadDatabase']))[1]
        if f_type not in allowed_file_types:
            return render(request, 'import.html', {'error': '{} is not an allowed file type!'.format(f_type)})

        if f_type == '.csv':
            file = request.FILES['uploadDatabase']
            decoded_file = file.read().decode('utf-8').splitlines()
            database_items = csv.DictReader(decoded_file)
            imported_headings = database_items.fieldnames

        # upload file
        upload_database = DatabaseUpload(account=attached_service, database=database_file, file_type=f_type)
        upload_database.save(database_file)

        # get pedigree model headings
        forbidden_pedigree_fields = ['id', 'creator', 'account', 'date_added']
        forbidden_pedigree_att_fields = ['id', 'account', 'custom_fields', 'reg_no']
        pedigree_headings = [field for field in Pedigree._meta.get_fields(include_parents=False, include_hidden=False) if field.name not in forbidden_pedigree_fields]
        pedigree_att_headings = [field for field in PedigreeAttributes._meta.get_fields(include_parents=False, include_hidden=False) if field.name not in forbidden_pedigree_att_fields]
        pedigree_headings = pedigree_headings + pedigree_att_headings

        # get breeder model headings
        forbidden_breeeder_fields = ['id', 'account', 'custom_fields']
        breeder_headings = [field for field in Breeder._meta.get_fields(include_parents=False, include_hidden=False)
                             if field.name not in forbidden_breeeder_fields]
        return render(request, 'analyse.html', {'imported_headings': imported_headings,
                                                'pedigree_headings': pedigree_headings,
                                                'breeder_headings': breeder_headings})
    return render(request, 'import.html')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_pedigree_data(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        db = DatabaseUpload.objects.filter(account=attached_service).latest('id')
        decoded_file = db.database.file.read().decode('utf-8').splitlines()
        database_items = csv.DictReader(decoded_file)
        date_fields = ['date_of_registration', 'dob', 'dod']
        post_data = {}

        # remove blank ('---') entries ###################
        for key, val in request.POST.items():
            if val == '---':
                if key in date_fields:
                    post_data[key] = None
                post_data[key] = ''
            else:
                post_data[key] = val

        # get all options ###################
        breeder = post_data['breeder'] or ''
        current_owner = post_data['current_owner'] or ''
        breed = post_data['breed'] or ''
        reg_no = post_data['reg_no'] or ''
        tag_no = post_data['tag_no'] or ''
        name = post_data['name'] or ''
        description = post_data['description'] or ''
        date_of_registration = post_data['date_of_registration'] or ''
        dob = post_data['dob'] or ''
        dod = post_data['dod'] or ''
        sex = post_data['sex'] or ''
        father = post_data['parent_father'] or ''
        father_notes = post_data['parent_father_notes'] or ''
        mother = post_data['parent_mother'] or ''
        mother_notes = post_data['parent_mother_notes'] or ''

        for row in database_items:
            # create breeder if it doesn't exist ###################
            if row[breeder] not in ('', None):
                breeder_obj, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[breeder], active=True)
            else:
                breeder_obj = None

            # create current owner if it doesn't exist ###################
            if row[current_owner] not in ('', None):
                current_owner_obj, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[current_owner], active=True)
            else:
                current_owner_obj = None

            # get or create parents ###################
            def get_or_create_parent(parent):
                if parent not in ('', None):
                    if Pedigree.objects.filter(account=attached_service, reg_no=parent).count() <= 1:
                        pedigree_object, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=parent)
                        return pedigree_object
                    else:
                        return Pedigree.objects.filter(account=attached_service, reg_no=parent).first()
                else:
                    return None

            try:
                father_obj = get_or_create_parent(row[father])
            except KeyError:
                father_obj = None

            try:
                mother_obj = get_or_create_parent(row[mother])
            except KeyError:
                mother_obj = None

            # convert dates ###################
            def convert_date(date):
                from django.utils.dateparse import parse_date
                if date not in ('', None):
                    try:
                        date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%d-%m-%y').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%d-%m-%Y').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%Y/%m/%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%y/%m/%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%d/%m/%y').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    try:
                        date = datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                    return parse_date(date)
                else:
                    return None

            try:
                date_of_registration_converted = convert_date(row[date_of_registration])
            except KeyError:
                date_of_registration_converted = None

            try:
                dob_converted = convert_date(row[dob])
            except KeyError:
                dob_converted = None

            try:
                dod_converted = convert_date(row[dod])
            except KeyError:
                dod_converted = None

            # create each new pedigree ###################
            pedigree, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=row[reg_no])
            pedigree.creator = request.user
            try:
                pedigree.breeder = breeder_obj
            except ValueError:
                pass
            except UnboundLocalError:
                pass
            #############################
            try:
                pedigree.current_owner = current_owner_obj
            except ValueError:
                pass
            except UnboundLocalError:
                pass
            #############################
            try:
                pedigree.tag_no = row[tag_no]
            except KeyError:
                pass
            #############################
            try:
                pedigree.name = row[name]
            except KeyError:
                pass
            #############################
            try:
                pedigree.description = row[description]
            except KeyError:
                pass
            #############################
            try:
                pedigree.date_of_registration = date_of_registration_converted
            except ValidationError:
                pass
            except KeyError:
                pass
            #############################
            try:
                pedigree.dob = dob_converted
            except ValidationError:
                pass
            except KeyError:
                pass
            #############################
            try:
                pedigree.dod = dod_converted
            except ValidationError:
                pass
            except KeyError:
                pass
            #############################
            try:
                pedigree.sex = row[sex]
            except KeyError:
                pass
            #############################
            try:
                pedigree.parent_father = father_obj
            except KeyError:
                pass
            #############################
            try:
                pedigree.parent_mother = mother_obj
            except KeyError:
                pass
            #############################
            try:
                pedigree.parent_father_notes = row[father_notes]
            except KeyError:
                pass
            #############################
            try:
                pedigree.parent_mother_notes = row[mother_notes]
            except KeyError:
                pass
            #############################

            pedigree.save()

            # create breed if it doesn't exist ###################
            if breed != '---':
                try:
                    breed_obj, created = Breed.objects.get_or_create(account=attached_service, breed_name=row[breed])
                except KeyError:
                    breed_obj = None
            else:
                breed_obj = None

            attributes, created = PedigreeAttributes.objects.get_or_create(reg_no=pedigree)
            try:
                attributes.breed = breed_obj
            except KeyError:
                pass
            attributes.custom_fields = attached_service.custom_fields
            attributes.save()
    return redirect('pedigree_search')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_breeder_data(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        db = DatabaseUpload.objects.filter(account=attached_service).latest('id')
        decoded_file = db.database.file.read().decode('utf-8').splitlines()
        database_items = csv.DictReader(decoded_file)

        post_data = {}

        # remove blank ('---') entries ###################
        for key, val in request.POST.items():
            if val == '---':
                post_data[key] = ''
            else:
                post_data[key] = val

        # get all options ###################
        breeding_prefix = post_data['breeding_prefix'] or ''
        contact_name = post_data['contact_name'] or ''
        address = post_data['address'] or ''
        phone_number1 = post_data['phone_number1'] or ''
        phone_number2 = post_data['phone_number2'] or ''
        email = post_data['email'] or ''
        active = post_data['active'] or ''

        # get or create each new pedigree ###################
        for row in database_items:
            breeder, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[breeding_prefix])

            try:
                breeder.contact_name = row[contact_name]
            except KeyError:
                pass
            ###################
            try:
                breeder.address = row[address]
            except KeyError:
                pass
            ###################
            try:
                breeder.phone_number1 = row[phone_number1]
            except KeyError:
                pass
            ###################
            try:
                breeder.phone_number2 = row[phone_number2]
            except KeyError:
                pass
            ###################
            try:
                breeder.email = row[email]
            except KeyError:
                pass
            ###################
            try:
                if row[active].title() in ('True', 'False'):
                    breeder.active = row[active].title()
                else:
                    pass
            except ValidationError:
                pass
            except KeyError:
                pass
            ###################

            breeder.save()
    return redirect('breeders')