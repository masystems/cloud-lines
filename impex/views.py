from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from pedigree.models import Pedigree, PedigreeImage
from pedigree.functions import get_pedigree_column_headings
from breeder.models import Breeder
from breed.models import Breed
from account.views import is_editor, get_main_account
from .models import DatabaseUpload, FileSlice
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
                        elif key == 'current_owner_id':
                            try:
                                current_owner = Breeder.objects.get(id=val)
                                current_owner_prefix = current_owner.breeding_prefix
                            except ObjectDoesNotExist:
                                current_owner_prefix = ""
                            row.append('{}'.format(current_owner_prefix))
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
                        elif key == 'sale_or_hire':
                            if pedigree.sale_or_hire:
                                row.append('yes')
                            else:
                                row.append('no')
                        # make sure 'None' isn't given for dates, and that they're formatted well
                        elif key == 'date_of_registration':
                            if pedigree.date_of_registration:
                                row.append(pedigree.date_of_registration.strftime('%d/%m/%Y'))
                            else:
                                row.append('')
                        elif key == 'dob':
                            if pedigree.dob:
                                row.append(pedigree.dob.strftime('%d/%m/%Y'))
                            else:
                                row.append('')
                        elif key == 'dod':
                            if pedigree.dod:
                                row.append(pedigree.dod.strftime('%d/%m/%Y'))
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
            # get header
            if request.POST.get('job'):
                # if we need to save the header
                if request.POST['job'] == 'header':
                    # flush the database upload down the digital toilet
                    DatabaseUpload.objects.filter(account=attached_service, user=request.user).delete()

                    # convert header to JSON
                    header = dumps({"header": request.POST.getlist('uploadDatabase[]')})

                    # errors is a dictionary to keep track of missing and invalid fields
                    errors = {}
                    # only mandatory fields are added to 
                    errors['missing'] = []
                    # only fields that need to be in a certain format are added to invalid fields
                    errors['invalid'] = []
                    
                    # create database upload object
                    database_upload = DatabaseUpload.objects.create(account=attached_service,
                                                                    header=header, user=request.user,
                                                                    errors=dumps(errors),
                                                                    total_lines=request.POST['totalLines'])
                    database_upload.save()
                    
                    return HttpResponse(dumps({'result': 'success'}))
                
                # if we need to save the body
                elif request.POST['job'] == 'slices':
                    
                    # create the file slice
                    file_slice = []
                    for key in request.POST:
                        if 'uploadDatabase' in key:
                            file_slice.append(request.POST.getlist(key))
                    
                    # save file slice
                    try:
                        file_slice = FileSlice.objects.create(database_upload=DatabaseUpload.objects.filter(account=attached_service, user=request.user).latest('id'), file_slice=dumps({'file_slice': file_slice}))
                    except Exception:
                        pass
                    
                    return HttpResponse(dumps({'result': 'success'}))
                    
        return render(request, 'import.html')
    else:
        return redirect('dashboard')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_data(request):
    attached_service = get_main_account(request.user)
    
    # get request, so display the page
    if request.method == 'GET':
        # if there is no relevant DatabaseUpload redirect to import
        if not DatabaseUpload.objects.filter(account=attached_service, user=request.user).exists():
            return redirect('import')

        # flush errors
        database_upload = DatabaseUpload.objects.filter(account=attached_service, user=request.user).latest('id')
        database_upload.errors = dumps({'missing': [], 'invalid': []})
        database_upload.save()
        
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

        # get imported headings
        imported_headings = loads(DatabaseUpload.objects.filter(account=attached_service, user=request.user).latest('id').header)['header']
        
        return render(request, 'analyse.html', {'imported_headings': imported_headings,
                                                'pedigree_headings': pedigree_headings,
                                                'breeder_headings': breeder_headings,
                                                'custom_fields': custom_field_names,
                                                'has_breeds': has_breeds,
                                                'breed_required': breed_required})
    
    return redirect('dashboard')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_pedigree_data(request):
    attached_service = get_main_account(request.user)
    
    if request.method == 'POST':
        # check if this is import or cancel - created not passed in if it's import
        if 'created' not in request.POST.keys():
            database_upload = DatabaseUpload.objects.filter(account=attached_service, user=request.user).latest('id')
            file_slice = FileSlice.objects.filter(database_upload=database_upload, used=False).earliest('id')

            # decoded_file = db.database.file.read().decode('utf-8').splitlines()
            # database_items = csv.DictReader(decoded_file)
            date_fields = ['date_of_registration', 'dob', 'dod']
            post_data = {}

            # get custom fields of account
            try:
                acc_custom_fields = loads(attached_service.custom_fields)
            except JSONDecodeError:
                acc_custom_fields = {}
            # get names of custom fields
            field_names = []
            for key, field in acc_custom_fields.items():
                field_names.append(field['fieldName'])
            
            # dictionary that stores name of given custom fields, and their column's index in the file header
            custom_fields_in = {}

            # iterate through columns
            for key, val in request.POST.items():
                # add custom field columns
                if key in field_names and val != '---':
                    # find what index of the header corresponds with this column
                    col_index = loads(database_upload.header)['header'].index(val)
                    # add name:index to list
                    custom_fields_in[key] = col_index
                
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
            sale_or_hire = post_data['sale_or_hire'] or ''

            # get index of each heading
            thousand = 1000
            if breeder:
                breeder = loads(database_upload.header)['header'].index(breeder)
            # if heading not given, make the index out of range (who's importing a thousand columns!?)
            else:
                breeder = thousand
            if current_owner:
                current_owner = loads(database_upload.header)['header'].index(current_owner)
            else:
                current_owner = thousand
            if breed:
                breed = loads(database_upload.header)['header'].index(breed)
            else:
                breed = thousand
            if reg_no:
                reg_no = loads(database_upload.header)['header'].index(reg_no)
            else:
                reg_no = thousand
            if tag_no:
                tag_no = loads(database_upload.header)['header'].index(tag_no)
            else:
                tag_no = thousand
            if name:
                name = loads(database_upload.header)['header'].index(name)
            else:
                name = thousand
            if description:
                description = loads(database_upload.header)['header'].index(description)
            else:
                description = thousand
            if date_of_registration:
                date_of_registration = loads(database_upload.header)['header'].index(date_of_registration)
            else:
                date_of_registration = thousand
            if dob:
                dob = loads(database_upload.header)['header'].index(dob)
            else:
                dob = thousand
            if dod:
                dod = loads(database_upload.header)['header'].index(dod)
            else:
                dod = thousand
            if sex:
                sex = loads(database_upload.header)['header'].index(sex)
            else:
                sex = thousand
            if born_as:
                born_as = loads(database_upload.header)['header'].index(born_as)
            else:
                born_as = thousand
            if status:
                status = loads(database_upload.header)['header'].index(status)
            else:
                status = thousand
            if father:
                father = loads(database_upload.header)['header'].index(father)
            else:
                father = thousand
            if father_notes:
                father_notes = loads(database_upload.header)['header'].index(father_notes)
            else:
                father_notes = thousand
            if mother:
                mother = loads(database_upload.header)['header'].index(mother)
            else:
                mother = thousand
            if mother_notes:
                mother_notes = loads(database_upload.header)['header'].index(mother_notes)
            else:
                mother_notes = thousand
            if sale_or_hire:
                sale_or_hire = loads(database_upload.header)['header'].index(sale_or_hire)
            else:
                sale_or_hire = thousand

            for row in loads(file_slice.file_slice)['file_slice']:
                # get row number, which is the last element of the row/list
                row_number = row[-1]
                
                # variable to store pedigree name or empty string
                if name != 1000:
                    ped_name = row[name]
                else:
                    ped_name = ''
                
                # get breeder. error if breeder doesn't exist or missing ###################
                try:
                    if row[breeder] not in ('', None):
                        breeder_obj = Breeder.objects.filter(account=attached_service, breeding_prefix=row[breeder].rstrip())
                        # error if breeder doesn't exist
                        if not breeder_obj.exists():
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'Breeder',
                                'row': row_number,
                                'name': ped_name,
                                'reason': f'breeder {row[breeder]} does not exist in the database - the breeder must be imported before you can import this pedigree'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                        # get the breeder
                        else:
                            breeder_obj = breeder_obj.first()
                    else:
                        breeder_obj = None
                        # error if missing
                        errors = loads(database_upload.errors)
                        errors['missing'].append({
                            'col': 'Breeder',
                            'row': row_number,
                            'name': ped_name
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                except IndexError:
                    breeder_obj = None

                # get current owner - error if if it doesn't exist ###################
                try:
                    if row[current_owner] not in ('', None):
                        current_owner_obj = Breeder.objects.filter(account=attached_service, breeding_prefix=row[current_owner].rstrip())
                        # error if owner doesn't exist
                        if not current_owner_obj.exists():
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'Current Owner',
                                'row': row_number,
                                'name': ped_name,
                                'reason': f'owner {row[current_owner]} does not exist in the database - the owner must be imported before you can import this pedigree'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                        else:
                            current_owner_obj = current_owner_obj.first()
                    else:
                        current_owner_obj = None
                        # error if missing
                        errors = loads(database_upload.errors)
                        errors['missing'].append({
                            'col': 'Current Owner',
                            'row': row_number,
                            'name': ped_name
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                except IndexError:
                    current_owner_obj = None

                # get or create pedigrees ###################
                def get_or_create_pedigree(pedigree, is_parent):
                    if pedigree not in ('', None):
                        if Pedigree.objects.filter(reg_no=pedigree).count() < 1:
                            # pedigree doesn't exist, so create one
                            # if parent, specify the sex appropriately
                            if is_parent == 'father':
                                pedigree_obj, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=pedigree, sex='male')
                            elif is_parent == 'mother':
                                pedigree_obj, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=pedigree, sex='female')
                            else:
                                pedigree_obj, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=pedigree)
                            
                            return pedigree_obj
                        else:
                            # get existing pedigree to be updated
                            ped = Pedigree.objects.get(reg_no=pedigree)
                            # check that the pedigree is for this account
                            if ped.account == attached_service:
                                return ped
                            # if not for account, create error, as the reg number is taken
                            else:
                                errors = loads(database_upload.errors)
                                errors['invalid'].append({
                                    'col': 'Registration Number',
                                    'row': row_number,
                                    'name': ped_name,
                                    'reason': 'this registration number is being used by another account - please specify a different one'
                                })
                                database_upload.errors = dumps(errors)
                                database_upload.save()
                                return None
                    else:
                        return None

                try:
                    father_obj = get_or_create_pedigree(row[father], 'father')
                except IndexError:
                    father_obj = None

                try:
                    mother_obj = get_or_create_pedigree(row[mother], 'mother')
                except IndexError:
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
                except IndexError:
                    date_of_registration_converted = None

                try:
                    dob_converted = convert_date(row[dob])
                except IndexError:
                    dob_converted = None

                try:
                    dod_converted = convert_date(row[dod])
                except IndexError:
                    dod_converted = None
                ############################# reg_no
                try:
                    if row[reg_no] == '':
                        errors = loads(database_upload.errors)
                        errors['missing'].append({
                            'col': 'Registration Number',
                            'row': row_number,
                            'name': ped_name
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                except IndexError:
                    pass

                # got or create each new pedigree ###################
                try:
                    # get or create pedigree
                    pedigree = get_or_create_pedigree(row[reg_no], False)
                except IndexError:
                    pass

                try:
                    pedigree.creator = request.user
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                
                try:
                    pedigree.breeder = breeder_obj
                except ValueError:
                    pass
                except UnboundLocalError:
                    pass
                except NameError:
                    pass
                except AttributeError:
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
                except AttributeError:
                    pass
                ############################# tag_no
                try:
                    pedigree.tag_no = row[tag_no]
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# name
                try:
                    pedigree.name = row[name]
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# description
                try:
                    pedigree.description = row[description]
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
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
                except AttributeError:
                    pass
                except UnboundLocalError:
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
                except AttributeError:
                    pass
                except UnboundLocalError:
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
                except AttributeError:
                    pass
                except UnboundLocalError:
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
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'Sex',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for sex, if given, must be one of "male", "female", or "castrated"'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                    # error if missing
                    else:
                        errors = loads(database_upload.errors)
                        errors['missing'].append({
                            'col': 'Sex',
                            'row': row_number,
                            'name': ped_name
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                        # delete pedigree if one was created
                        if pedigree.id:
                            pedigree.delete()
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
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
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'Born As',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for born as, if given, must be one of "single", "twin", "triplet", or "quad"'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# status
                try:
                    # if status given
                    if row[status] != '':
                        # if it's valid, save it
                        if row[status].lower() in ('dead', 'alive', 'unknown'):
                            pedigree.status = row[status].lower()
                        # invalid, so add error
                        else:
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'Status',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for status, if given, must be one of "dead", "alive", or "unknown"'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                    # error if missing
                    else:
                        errors = loads(database_upload.errors)
                        errors['missing'].append({
                            'col': 'Status',
                            'row': row_number,
                            'name': ped_name
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                        # delete pedigree if one was created
                        if pedigree.id:
                            pedigree.delete()
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# father
                try:
                    pedigree.parent_father = father_obj
                except KeyError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# mother
                try:
                    pedigree.parent_mother = mother_obj
                except KeyError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# father notes
                try:
                    pedigree.parent_father_notes = row[father_notes]
                except IndexError:
                    try:
                        pedigree.parent_father_notes = ''
                    except AttributeError:
                        pass
                    except UnboundLocalError:
                        pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# mother notes
                try:
                    pedigree.parent_mother_notes = row[mother_notes]
                except IndexError:
                    try:
                        pedigree.parent_mother_notes = ''
                    except AttributeError:
                        pass
                    except UnboundLocalError:
                        pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass
                ############################# sale or hire
                try:
                    # if sale_or_hire given
                    if row[sale_or_hire] != '':
                        # if it's valid, save it
                        if row[sale_or_hire].lower() in ('yes', 'no'):
                            if row[sale_or_hire].lower() == 'yes':
                                pedigree.sale_or_hire = True
                            else:
                                pedigree.sale_or_hire = False
                        # invalid, so add error
                        else:
                            errors = loads(database_upload.errors)
                            errors['invalid'].append({
                                'col': 'For Sale/Hire',
                                'row': row_number,
                                'name': ped_name,
                                'reason': 'the input for sale/hire, if given, must be "yes" or "no"'
                            })
                            database_upload.errors = dumps(errors)
                            database_upload.save()
                            # delete pedigree if one was created
                            if pedigree.id:
                                pedigree.delete()
                except IndexError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass

                #################### breed
                # not organisation
                if attached_service.service.service_name != 'Organisation':
                    breed_obj = Breed.objects.filter(account=attached_service).first()
                    # error if given breed doesn't match account breed, if given
                    if breed != '':
                        try:
                            if breed_obj.breed_name != row[breed] and row[breed] != '':
                                errors = loads(database_upload.errors)
                                errors['invalid'].append({
                                    'col': 'Breed',
                                    'row': row_number,
                                    'name': ped_name,
                                    'reason': 'the input for breed, if given, must be the breed created for your account - to create more breeds, you need to <a href="/account/profile">upgrade your account</a>'
                                })
                                database_upload.errors = dumps(errors)
                                database_upload.save()
                        except IndexError:
                            pass
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
                                errors = loads(database_upload.errors)
                                errors['invalid'].append({
                                    'col': 'Breed',
                                    'row': row_number,
                                    'name': ped_name,
                                    'reason': 'the input for breed must be one of the breeds created for your account - you can create more breeds via the <a href="/breeds">Breed</a> page'
                                })
                                database_upload.errors = dumps(errors)
                                database_upload.save()
                    except IndexError:
                        breed_obj = None
                else:
                    breed_obj = None

                try:
                    pedigree.breed = breed_obj
                except KeyError:
                    pass
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass

                ############################# custom
                for cf_name, cf_index in custom_fields_in.items():
                    # iterate through account custom fields
                    for id, field in acc_custom_fields.items():
                        if acc_custom_fields[id]['fieldName'] == cf_name:
                            try:
                                # populate with value from the imported csv file
                                acc_custom_fields[id]['field_value'] = row[cf_index]
                            except IndexError:
                                pass
                
                try:
                    pedigree.custom_fields = dumps(acc_custom_fields)
                    
                    pedigree.save()
                except NameError:
                    pass
                except AttributeError:
                    pass
                except UnboundLocalError:
                    pass

            # mark the slice just processed as used
            file_slice.used = True
            file_slice.save()
            
            # if we have exceeded the max number of errors, stop the import and go back to analyse page
            if len(loads(database_upload.errors)['missing']) + len(loads(database_upload.errors)['invalid']) > 50:

                errors = loads(database_upload.errors)
                
                # it's over so delete DatabaseUpload
                database_upload.delete()
                
                # put any Breed errors (where they need to create a breed) to the top
                breed_errors = []
                # extract the breed errors
                for invalid_error in errors['invalid']:
                    if invalid_error['col'] == 'Breed':
                        breed_errors.append(invalid_error)
                # put the breed errors to the front of the errors
                for breed_error in breed_errors:
                    errors['invalid'].remove(breed_error)
                    errors['invalid'].insert(0, breed_error)
                
                # make sure we don't send so many errors that a 500 error is caused
                errors['invalid'] = errors['invalid'][:50]
                errors['missing'] = errors['missing'][:50]

                return HttpResponse(dumps({'result': 'incomplete', 'errors': errors}))
            
            # check whether there are any more file slices left. if there are, tell the browser to go again
            elif FileSlice.objects.filter(database_upload=database_upload, used=False).exists():
                completed_lines = FileSlice.objects.filter(database_upload=database_upload, used=True).count() * 200
                remaining_lines = database_upload.total_lines - completed_lines
                return HttpResponse(dumps({'result': 'again',
                                           'completed': completed_lines,
                                           'remaining': remaining_lines}))
            
            # import completed with errors
            elif len(loads(database_upload.errors)['missing']) + len(loads(database_upload.errors)['invalid']) > 0:

                errors = loads(database_upload.errors)
                
                # it's over so delete DatabaseUpload
                database_upload.delete()
                
                # put any Breed errors (where they need to create a breed) to the top
                breed_errors = []
                # extract the breed errors
                for invalid_error in errors['invalid']:
                    if invalid_error['col'] == 'Breed':
                        breed_errors.append(invalid_error)
                # put the breed errors to the front of the errors
                for breed_error in breed_errors:
                    errors['invalid'].remove(breed_error)
                    errors['invalid'].insert(0, breed_error)
                
                # make sure we don't send so many errors that a 500 error is caused
                errors['invalid'] = errors['invalid'][:50]
                errors['missing'] = errors['missing'][:50]

                return HttpResponse(dumps({'result': 'complete', 'errors': errors}))
            
            # import completed with no errors
            else:
                # it's over so delete DatabaseUpload
                database_upload.delete()

                return HttpResponse(dumps({'result': 'success'}))

        
        # cancel import by deleting the created objects
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
        
        database_upload = DatabaseUpload.objects.filter(account=attached_service, user=request.user).latest('id')
        file_slice = FileSlice.objects.filter(database_upload=database_upload, used=False).earliest('id')

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

        # get index of each heading
        thousand = 1000
        if breeding_prefix:
            breeding_prefix = loads(database_upload.header)['header'].index(breeding_prefix)
        # if heading not given, make the index out of range (who's importing a thousand columns!?)
        else:
            breeding_prefix = thousand
        if contact_name:
            contact_name = loads(database_upload.header)['header'].index(contact_name)
        else:
            contact_name = thousand
        if address:
            address = loads(database_upload.header)['header'].index(address)
        else:
            address = thousand
        if phone_number1:
            phone_number1 = loads(database_upload.header)['header'].index(phone_number1)
        else:
            phone_number1 = thousand
        if phone_number2:
            phone_number2 = loads(database_upload.header)['header'].index(phone_number2)
        else:
            phone_number2 = thousand
        if email:
            email = loads(database_upload.header)['header'].index(email)
        else:
            email = thousand
        if active:
            active = loads(database_upload.header)['header'].index(active)
        else:
            active = thousand

        # regex pattern used to validate email
        email_pattern = re.compile('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')

        # get or create each new pedigree ###################
        for row in loads(file_slice.file_slice)['file_slice']:
            row_number = row[-1]
            
            # set name for error messages
            if contact_name != thousand:
                name = row[contact_name]
            else:
                name = ''

            ################### breeding prefix
            # check it is not empty
            if row[breeding_prefix] == '':
                errors = loads(database_upload.errors)
                errors['missing'].append({
                    'col': 'Breeding Prefix',
                    'row': row_number,
                    'name': name
                })
                database_upload.errors = dumps(errors)
                database_upload.save()
            # create a new breeder
            breeder, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[breeding_prefix].rstrip())
            ################### contact name
            try:
                breeder.contact_name = row[contact_name]
            except IndexError:
                pass
            except UnboundLocalError:
                pass
            ################### address
            try:
                breeder.address = row[address]
            except IndexError:
                pass
            except UnboundLocalError:
                pass
            ################### phone_number1
            try:
                breeder.phone_number1 = row[phone_number1]
            except IndexError:
                pass
            except UnboundLocalError:
                pass
            ################### phone_number2
            try:
                breeder.phone_number2 = row[phone_number2]
            except IndexError:
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
                        errors = loads(database_upload.errors)
                        errors['invalid'].append({
                            'col': 'Email',
                            'row': row_number,
                            'name': name,
                            'reason': 'the email given is invalid'
                        })
                        database_upload.errors = dumps(errors)
                        database_upload.save()
                        # delete breeder if one was created
                        if breeder.id:
                            breeder.delete()
            except IndexError:
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
                    errors = loads(database_upload.errors)
                    errors['invalid'].append({
                        'col': 'Status',
                        'row': row_number,
                        'name': name,
                        'reason': 'status must be "Active" or "Inactive" - if left blank, it defaults to "Inactive"'
                    })
                    database_upload.errors = dumps(errors)
                    database_upload.save()
                    # delete breeder if one was created
                    if breeder.id:
                        breeder.delete()
            except ValidationError:
                pass
            except IndexError:
                pass
            except UnboundLocalError:
                pass
            ###################
            # save the breeder
            try:
                breeder.save()
            except NameError:
                pass
        
        # set the file just processed to used
        file_slice.used = True
        file_slice.save()
        
        # if the max number of errors was exceded, stop the import and redirect back to analyse page
        if len(loads(database_upload.errors)['missing']) + len(loads(database_upload.errors)['invalid']) > 50:

            # it's over so delete DatabaseUpload
            database_upload.delete()

            # make sure we don't send so many errors that a 500 error is caused
            errors = loads(database_upload.errors)
            errors['invalid'] = errors['invalid'][:50]
            errors['missing'] = errors['missing'][:50]

            return HttpResponse(dumps({'result': 'incomplete', 'errors': errors}))
        
        # check whether there are any more left. if there are, tell the browser to go again
        elif FileSlice.objects.filter(database_upload=database_upload, used=False).exists():
            completed_lines = FileSlice.objects.filter(database_upload=database_upload, used=True).count() * 200
            remaining_lines = database_upload.total_lines - completed_lines
            return HttpResponse(dumps({'result': 'again',
                                        'completed': completed_lines,
                                        'remaining': remaining_lines}))
        
        # if there were errors, redirect back to analyse page
        elif len(loads(database_upload.errors)['missing']) + len(loads(database_upload.errors)['invalid']) > 0:

            # it's over so delete DatabaseUpload
            database_upload.delete()

            # make sure we don't send so many errors that a 500 error is caused
            errors = loads(database_upload.errors)
            errors['invalid'] = errors['invalid'][:50]
            errors['missing'] = errors['missing'][:50]

            return HttpResponse(dumps({'result': 'complete', 'errors': errors}))
        else:
            # it's over so delete DatabaseUpload
            database_upload.delete()
            
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
