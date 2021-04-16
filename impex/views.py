from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from pedigree.models import Pedigree, PedigreeImage
from pedigree.functions import get_pedigree_column_headings
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_main_account
from .models import DatabaseUpload
from datetime import datetime
from os.path import splitext
import csv
from json import loads, dumps, JSONDecodeError
import re


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def export(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        #fields = request.POST.getlist('fields')
        #print(fields)
        date = datetime.now()
        if request.POST['submit'] == 'xlsx':
            pass
        elif request.POST['submit'] == 'csv':
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="cloud-lines-pedigrees-{}.csv"'.format(date.strftime("%Y-%m-%d"))

            writer = csv.writer(response)
            header = False

            for pedigree in Pedigree.objects.filter(account=attached_service):
                head = []
                row = []
                for key, val in pedigree.__dict__.items():
                    if key not in ('_state', 'state', 'id', 'creator_id', 'account_id', 'breed_group', 'date_added'):
                        # load custom fields
                        if key == 'custom_fields':
                            try:
                                custom_fields = dict(loads(pedigree.custom_fields)).values()
                            except JSONDecodeError:
                                custom_fields = {}
                        
                        if not header:
                            if key == 'custom_fields':
                                # add a columns for each custom field
                                for field in custom_fields:
                                    head.append(field['fieldName'])
                            else:
                                # use verbose names of the pedigree fields as field names
                                head.append(Pedigree._meta.get_field(key).verbose_name)
                        
                        if key == 'parent_mother_id' or key == 'parent_father_id':
                            try:
                                parent = Pedigree.objects.get(id=val)
                                reg_no = parent.reg_no.strip()
                            except ObjectDoesNotExist:
                                reg_no = ""
                            row.append('{}'.format(reg_no))
                        elif key == 'breeder_id':
                            try:
                                breeder = Breeder.objects.get(id=val)
                                breed_prefix = breeder.breeding_prefix
                            except ObjectDoesNotExist:
                                breed_prefix = ""
                            row.append('{}'.format(breed_prefix))
                        elif key == 'breed_id':
                            try:
                                breed = Breed.objects.get(id=val)
                                breed_name = breed.breed_name
                            except ObjectDoesNotExist:
                                breed_name = ""
                            row.append('{}'.format(breed_name))
                        elif key == 'custom_fields':
                            # populate each custom field column with the value
                            for field in custom_fields:
                                if 'field_value' in field:
                                    row.append(field['field_value'])
                                else:
                                    row.append('')
                        else:
                            row.append('{}'.format(val))
                if not header:
                    writer.writerow(head)
                    header = True
                writer.writerow(row)

            return response
        elif request.POST['submit'] == 'pdf':
            pass

    return render(request, 'export.html', {'fields': Pedigree._meta.get_fields(include_parents=False, include_hidden=False)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def importx(request):
    attached_service = get_main_account(request.user)
    if request.user in attached_service.admin_users.all() or request.user == attached_service.user.user:
        allowed_file_types = ('.csv')
        if request.method == 'POST':

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

            # check if file is empty
            if file.size <= 1:
                return render(request, 'import.html', {'error': '{} is empty!'.format(request.FILES['uploadDatabase'])})

            # upload file
            upload_database = DatabaseUpload(account=attached_service, database=database_file, file_type=f_type)
            upload_database.save(database_file)

            # get pedigree model headings
            pedigree_headings = get_pedigree_column_headings()

            # get breeder model headings
            forbidden_breeeder_fields = ['id', 'account', 'custom_fields']
            breeder_headings = [field for field in Breeder._meta.get_fields(include_parents=False, include_hidden=False)
                                 if field.name not in forbidden_breeeder_fields]

            # get custom fields
            try:
                custom_fields = dict(loads(attached_service.custom_fields)).values()
            except JSONDecodeError:
                custom_fields = {}
            custom_field_names = []
            for field in custom_fields:
                custom_field_names.append(field['fieldName'])

            # see if any breeds have been set up
            has_breeds = Breed.objects.filter(account=attached_service).count() > 0

            # breed is required if org account with multiple breeds
            if attached_service.service.service_name == 'Organisation' and Breed.objects.filter(account=attached_service).count() > 1:
                breed_required = 'yes'
            else:
                breed_required = 'no'

            return render(request, 'analyse.html', {'imported_headings': imported_headings,
                                                    'pedigree_headings': pedigree_headings,
                                                    'breeder_headings': breeder_headings,
                                                    'custom_fields': custom_field_names,
                                                    'has_breeds': has_breeds,
                                                    'breed_required': breed_required})
        return render(request, 'import.html')
    else:
        return redirect('dashboard')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_pedigree_data(request):
    if request.method == 'POST':
        # check if this is import or cancel
        if 'created' not in request.POST.keys():
            attached_service = get_main_account(request.user)
            db = DatabaseUpload.objects.filter(account=attached_service).latest('id')
            decoded_file = db.database.file.read().decode('utf-8').splitlines()
            database_items = csv.DictReader(decoded_file)
            date_fields = ['date_of_registration', 'dob', 'dod']
            post_data = {}

            # get custom fields of account
            try:
                acc_custom_fields = loads(attached_service.custom_fields)
            except json.decoder.JSONDecodeError:
                acc_custom_fields = {}
            # get names of custom fields
            field_names = []
            for key, field in acc_custom_fields.items():
                field_names.append(field['fieldName'])
            custom_fields_in = []

            # iterate through columns
            for key, val in request.POST.items():
                # add custom field columns
                if key in field_names:
                    custom_fields_in.append(key)
                
                # remove blank ('---') entries ###################
                elif val == '---':
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
            born_as = post_data['born_as'] or ''
            status = post_data['status'] or ''
            father = post_data['parent_father'] or ''
            father_notes = post_data['parent_father_notes'] or ''
            mother = post_data['parent_mother'] or ''
            mother_notes = post_data['parent_mother_notes'] or ''

            # errors is a dictionary to keep track of missing and invalid fields
            errors = {}
            # only mandatory fields are added to 
            errors['missing'] = []
            # only fields that need to be in a certain format are added to invalid fields
            errors['invalid'] = []

            # existing pedigrees can be added, but with a warning
            existing = []

            # list to store created objects so they can be deleted if there are errors
            created_objects = []

            row_number = 1
            for row in database_items:
                row_number += 1
                
                # variable to store pedigree name or empty string
                if name:
                    ped_name = row[name]
                else:
                    ped_name = ''
                
                # get breeder. error if breeder doesn't exist or missing ###################
                try:
                    if row[breeder] not in ('', None):
                        breeder_obj = Breeder.objects.filter(account=attached_service, breeding_prefix=row[breeder].rstrip())
                        # error if breeder doesn't exist
                        if not breeder_obj.exists():
                            errors['invalid'].append({
                                'col': 'Breeder',
                                'row': row_number,
                                'name': ped_name,
                                'reason': f'breeder {row[breeder]} does not exist in the database - the breeder must be imported before you can import this pedigree'
                            })
                    else:
                        breeder_obj = None
                        # error if missing
                        errors['missing'].append({
                            'col': 'Breeder',
                            'row': row_number,
                            'name': ped_name
                        })
                except KeyError:
                    breeder_obj = None

                # get current owner - error if if it doesn't exist ###################
                try:
                    if row[current_owner] not in ('', None):
                        current_owner_obj = Breeder.objects.filter(account=attached_service, breeding_prefix=row[current_owner].rstrip())
                        # error if owner doesn't exist
                        if not current_owner_obj.exists():
                            errors['invalid'].append({
                                'col': 'Current Owner',
                                'row': row_number,
                                'name': ped_name,
                                'reason': f'owner {row[current_owner]} does not exist in the database - the owner must be imported before you can import this pedigree'
                            })
                    else:
                        current_owner_obj = None
                except KeyError:
                    current_owner_obj = None

                # get or create pedigrees ###################
                def get_or_create_pedigree(pedigree):
                    if pedigree not in ('', None):
                        if Pedigree.objects.filter(account=attached_service, reg_no=pedigree).count() < 1:
                            # pedigree doesn't exist, so create one
                            pedigree_obj =  Pedigree.objects.create(account=attached_service, reg_no=pedigree)
                            created_objects.append(pedigree_obj)
                            return pedigree_obj
                        else:
                            # pedigree does exist, so get it
                            return Pedigree.objects.filter(account=attached_service, reg_no=pedigree).first()
                    else:
                        return None

                try:
                    father_obj = get_or_create_pedigree(row[father])
                except KeyError:
                    father_obj = None

                try:
                    mother_obj = get_or_create_pedigree(row[mother])
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
                ############################# reg_no
                if row[reg_no] == '':
                    errors['missing'].append({
                        'col': 'Registration Number',
                        'row': row_number,
                        'name': ped_name
                    })

                # create each new pedigree if no errors found in file ###################
                if len(errors['missing']) == 0 and len(errors['invalid']) == 0:
                    # add to existing if this pedigree already exists
                    if Pedigree.objects.filter(account=attached_service, reg_no=row[reg_no]).count() > 0:
                        existing.append({
                            'row': row_number,
                            'name': ped_name,
                            'reg_no': row[reg_no]
                        })
                    
                    # get or create pedigree
                    pedigree = get_or_create_pedigree(row[reg_no])

                try:
                    pedigree.creator = request.user
                except NameError:
                    pass
                
                try:
                    pedigree.breeder = breeder_obj
                except ValueError:
                    pass
                except UnboundLocalError:
                    pass
                except NameError:
                    pass
                ############################# owner
                try:
                    pedigree.current_owner = current_owner_obj
                except ValueError:
                    pass
                except UnboundLocalError:
                    pass
                except NameError:
                    pass
                ############################# tag_no
                try:
                    pedigree.tag_no = row[tag_no]
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# name
                try:
                    pedigree.name = row[name]
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# description
                try:
                    pedigree.description = row[description]
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# dor
                try:
                    pedigree.date_of_registration = date_of_registration_converted
                except ValidationError:
                    pass
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# dob
                try:
                    pedigree.dob = dob_converted
                except ValidationError:
                    pass
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# dod
                try:
                    pedigree.dod = dod_converted
                except ValidationError:
                    pass
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# sex
                try:
                    # if sex given
                    if row[sex] != '':
                        # if it's valid, save it
                        if row[sex].lower() in ('male', 'female', 'castrated'):
                            pedigree.sex = row[sex]
                        # invalid, so add error
                        else:
                            errors['invalid'].append({
                                'col': 'Sex',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for sex, if given, must be one of "male", "female", or "castrated"'
                            })
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                    # error if missing
                    else:
                        errors['missing'].append({
                            'col': 'Sex',
                            'row': row_number,
                            'name': ped_name
                        })
                        # delete pedigree if one was created
                        if pedigree.id:
                            pedigree.delete()
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# born as
                try:
                    # if born_as given
                    if row[born_as] != '':
                        # if it's valid, save it
                        if row[born_as].lower() in ('single', 'twin', 'triplet', 'quad'):
                            pedigree.born_as = row[born_as]
                        # invalid, so add error
                        else:
                            errors['invalid'].append({
                                'col': 'Born As',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for born as, if given, must be one of "single", "twin", "triplet", or "quad"'
                            })
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# status
                try:
                    # if status given
                    if row[status] != '':
                        # if it's valid, save it
                        if row[status].lower() in ('dead', 'alive', 'unknown'):
                            pedigree.status = row[status]
                        # invalid, so add error
                        else:
                            errors['invalid'].append({
                                'col': 'Status',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for status, if given, must be one of "dead", "alive", or "unknown"'
                            })
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                    # error if missing
                    else:
                        errors['missing'].append({
                            'col': 'Status',
                            'row': row_number,
                            'name': ped_name
                        })
                        # delete pedigree if one was created
                        if pedigree.id:
                            pedigree.delete()
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# father
                try:
                    pedigree.parent_father = father_obj
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# mother
                try:
                    pedigree.parent_mother = mother_obj
                except KeyError:
                    pass
                except NameError:
                    pass
                ############################# father notes
                try:
                    pedigree.parent_father_notes = row[father_notes]
                except KeyError:
                    pedigree.parent_father_notes = ''
                except NameError:
                    pass
                ############################# mother notes
                try:
                    pedigree.parent_mother_notes = row[mother_notes]
                except KeyError:
                    pedigree.parent_mother_notes = ''
                except NameError:
                    pass
                #############################

                #################### breed
                # not organisation
                if attached_service.service.service_name != 'Organisation':
                    breed_obj = Breed.objects.filter(account=attached_service).first()
                    # error if given breed doesn't match account breed, if given
                    if breed != '':
                        if breed_obj.breed_name != row[breed] and row[breed] != '':
                            errors['invalid'].append({
                                'col': 'Breed',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for breed, if given, must be the breed created for your account - to create more breeds, you need to <a href="/account/profile">upgrade your account</a>'
                            })
                # organisation
                elif breed != '---':
                    try:
                        # check if breed exists
                        if Breed.objects.filter(account=attached_service, breed_name=row[breed]).count() > 0:
                            breed_obj = Breed.objects.filter(account=attached_service, breed_name=row[breed]).first()
                        # error if breed not been created
                        else:
                            breed_obj = None
                            if row[breed] != '':
                                errors['invalid'].append({
                                    'col': 'Breed',
                                    'row': row_number,
                                    'name': ped_name,
                                    'reason': 'the input for breed must be one of the breeds created for your account - you can create more breeds via the <a href="/breeds">Breed</a> page'
                                })
                    except KeyError:
                        breed_obj = None
                else:
                    breed_obj = None

                try:
                    pedigree.breed = breed_obj
                except KeyError:
                    pass
                except NameError:
                    pass

                ############################# custom
                for cf_col in custom_fields_in:
                    # iterate through account custom fields
                    for id, field in acc_custom_fields.items():
                        if acc_custom_fields[id]['fieldName'] == cf_col:
                            # populate with value from the imported csv file
                            acc_custom_fields[id]['field_value'] = row[cf_col]
                
                try:
                    pedigree.custom_fields = dumps(acc_custom_fields)
                    
                    pedigree.save()
                except NameError:
                    pass

            # if there were errors, delete any breeders that were saved (before invalid/missing fields were found),
            # , and redirect back to analyse page
            if len(errors['missing']) > 0 or len(errors['invalid']) > 0:
                for created_object in created_objects:
                    if created_object.id:
                        created_object.delete()

                return HttpResponse(dumps({'result': 'fail', 'errors': errors}))
            # need to warn user if they specified any pedigrees that already exist
            elif len(existing) > 0:
                # get and pass in ids of created objects so it is known what to delete if user cancels
                created = []
                for created_object in created_objects:
                    if created_object.id:
                        created.append(created_object.id)

                return HttpResponse(dumps({'result': 'existing', 'existing': existing, 'created': created}))
            else:
                return HttpResponse(dumps({'result': 'success'}))

        
        # cancel import
        else:
            for obj_id in list(request.POST.get('created').split(',')):
                if obj_id:
                    if Pedigree.objects.filter(id=int(obj_id)).count() > 0:
                        Pedigree.objects.filter(id=int(obj_id)).first().delete()

            return HttpResponse()
    
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

        # regex pattern used to validate email
        email_pattern = re.compile('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')

        # errors is a dictionary to keep track of missing and invalid fields
        errors = {}
        # only mandatory fields are added to 
        errors['missing'] = []
        # only fields that need to be in a certain format are added to invalid fields
        errors['invalid'] = []

        # list of breeders saved into the DB
        saved_breeders = []
        row_number = 1
        # get or create each new pedigree ###################
        for row in database_items:
            row_number += 1

            # set name for error messages
            if contact_name:
                name = row[contact_name]
            else:
                name = ''

            ################### breeding prefix
            # check it is not empty
            if row[breeding_prefix] == '':
                errors['missing'].append({
                    'col': 'Breeding Prefix',
                    'row': row_number,
                    'name': name
                })
            # check prefix doesn't yet exist in the database
            elif Breeder.objects.filter(breeding_prefix=row[breeding_prefix]).exists():
                errors['invalid'].append({
                    'col': 'Breeding Prefix',
                    'row': row_number,
                    'name': name,
                    'reason': 'a breeder with this prefix already exists'
                })
            # check no data is missing/invalid before creating a new breeder
            elif len(errors['missing']) == 0 and len(errors['invalid']) == 0:
                breeder, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[breeding_prefix].rstrip())
            ################### contact name
            try:
                breeder.contact_name = row[contact_name]
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ################### address
            try:
                breeder.address = row[address]
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ################### phone_number1
            try:
                breeder.phone_number1 = row[phone_number1]
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ################### phone_number2
            try:
                breeder.phone_number2 = row[phone_number2]
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ################### email
            try:
                # if email given
                if row[email] != '':
                    # validate email
                    if email_pattern.match(row[email]):
                        breeder.email = row[email]
                    # add to errors invalid
                    else:
                        errors['invalid'].append({
                            'col': 'Email',
                            'row': row_number,
                            'name': name,
                            'reason': 'the email given is invalid'
                        })
                        # delete breeder if one was created
                        if breeder.id:
                            breeder.delete()
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ################### active
            try:
                if row[active].title() == 'Active':
                    breeder.active = True
                elif row[active].title() == 'Inactive':
                    breeder.active = False
                # add to invalid if content was invalid
                elif row[active] != '':
                    errors['invalid'].append({
                        'col': 'Status',
                        'row': row_number,
                        'name': name,
                        'reason': 'status must be "Active" or "Inactive" - if left blank, it defaults to "Inactive"'
                    })
                    # delete breeder if one was created
                    if breeder.id:
                        breeder.delete()
            except ValidationError:
                pass
            except KeyError:
                pass
            except UnboundLocalError:
                pass
            ###################
            # check that no rows are invalid before saving the breeder and adding to saved_breeders list
            if len(errors['missing']) == 0 and len(errors['invalid']) == 0:
                breeder.save()
                saved_breeders.append(breeder)
        # if there were errors, delete any breeders that were created (before invalid/missing fields were found),
        # , and redirect back to analyse page
        if len(errors['missing']) > 0 or len(errors['invalid']) > 0:
            for saved_breeder in saved_breeders:
                if saved_breeder.id:
                    saved_breeder.delete()

            return HttpResponse(dumps({'result': 'fail', 'errors': errors}))
        else:
            return HttpResponse(dumps({'result': 'success'}))

    return redirect('breeders')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def image_import(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        images = request.FILES.getlist('file')
        for image in images:
            filename, file_extension = splitext(str(image))
            try:
                pedigree = Pedigree.objects.get(account=attached_service, reg_no=filename)
                upload = PedigreeImage(account=attached_service, image=image, reg_no=pedigree)
                upload.save()
            except Pedigree.DoesNotExist:
                pass

        return HttpResponse('')
    return redirect('import')
