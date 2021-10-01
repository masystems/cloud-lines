from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.db.models import Q
from .models import Pedigree
from account.views import is_editor, get_main_account, has_permission
from .functions import get_site_pedigree_column_headings
from json import dumps
from django.urls import reverse
from .views import update_pedigree_cf


@login_required(login_url='/accounts/login/')
def get_pedigrees(request):
    attached_service = get_main_account(request.user)
    columns, column_data = get_site_pedigree_column_headings(attached_service)
    start = int(request.POST.get('start', 0))
    end = int(request.POST.get('length', 20))
    search = request.POST.get('search[value]', "")
    sort_by = request.POST.get(f'columns[{request.POST.get("order[0][column]")}][data]')

    # get the values of the column search fields
    # breeder search
    if 'breeder' in attached_service.pedigree_columns.split(','):
        breeder_index = int(attached_service.pedigree_columns.split(',').index('breeder')) + 1
        breeder_search = request.POST.get(f'columns[{breeder_index}][search][value]')
    else:
        breeder_search = ''
    # current owner search
    if 'current_owner' in attached_service.pedigree_columns.split(','):
        owner_index = int(attached_service.pedigree_columns.split(',').index('current_owner')) + 1
        owner_search = request.POST.get(f'columns[{owner_index}][search][value]')
    else:
        owner_search = ''
    # reg_no search
    if 'reg_no' in attached_service.pedigree_columns.split(','):
        reg_no_index = int(attached_service.pedigree_columns.split(',').index('reg_no')) + 1
        reg_no_search = request.POST.get(f'columns[{reg_no_index}][search][value]')
    else:
        reg_no_search = ''
    # tag_no search
    if 'tag_no' in attached_service.pedigree_columns.split(','):
        tag_no_index = int(attached_service.pedigree_columns.split(',').index('tag_no')) + 1
        tag_no_search = request.POST.get(f'columns[{tag_no_index}][search][value]')
    else:
        tag_no_search = ''
    # name_search
    if 'name' in attached_service.pedigree_columns.split(','):
        name_index = int(attached_service.pedigree_columns.split(',').index('name')) + 1
        name_search = request.POST.get(f'columns[{name_index}][search][value]')
    else:
        name_search = ''
    # description_search
    if 'description' in attached_service.pedigree_columns.split(','):
        desc_index = int(attached_service.pedigree_columns.split(',').index('description')) + 1
        desc_search = request.POST.get(f'columns[{desc_index}][search][value]')
    else:
        desc_search = ''
    # date_of_registration_search
    if 'date_of_registration' in attached_service.pedigree_columns.split(','):
        dor_index = int(attached_service.pedigree_columns.split(',').index('date_of_registration')) + 1
        dor_search_list = request.POST.get(f'columns[{dor_index}][search][value]').split('-')
        if len(dor_search_list) == 3:
            dor_search = f'{dor_search_list[2]}-{dor_search_list[1]}-{dor_search_list[0]}'
        elif len(dor_search_list) == 2:
            dor_search = f'{dor_search_list[1]}-{dor_search_list[0]}'
        else:
            dor_search = dor_search_list[0]
    else:
        dor_search = ''
    # dob_search
    if 'dob' in attached_service.pedigree_columns.split(','):
        dob_index = int(attached_service.pedigree_columns.split(',').index('dob')) + 1
        dob_search_list = request.POST.get(f'columns[{dob_index}][search][value]').split('-')
        if len(dob_search_list) == 3:
            dob_search = f'{dob_search_list[2]}-{dob_search_list[1]}-{dob_search_list[0]}'
        elif len(dob_search_list) == 2:
            dob_search = f'{dob_search_list[1]}-{dob_search_list[0]}'
        else:
            dob_search = dob_search_list[0]
    else:
        dob_search = ''
    # dod_search
    if 'dod' in attached_service.pedigree_columns.split(','):
        dod_index = int(attached_service.pedigree_columns.split(',').index('dod')) + 1
        dod_search_list = request.POST.get(f'columns[{dod_index}][search][value]').split('-')
        if len(dod_search_list) == 3:
            dod_search = f'{dod_search_list[2]}-{dod_search_list[1]}-{dod_search_list[0]}'
        elif len(dod_search_list) == 2:
            dod_search = f'{dod_search_list[1]}-{dod_search_list[0]}'
        else:
            dod_search = dod_search_list[0]
    else:
        dod_search = ''
    # status_search
    if 'status' in attached_service.pedigree_columns.split(','):
        status_index = int(attached_service.pedigree_columns.split(',').index('status')) + 1
        status_search = request.POST.get(f'columns[{status_index}][search][value]')
    else:
        status_search = ''
    # sex_search
    if 'sex' in attached_service.pedigree_columns.split(','):
        sex_index = int(attached_service.pedigree_columns.split(',').index('sex')) + 1
        sex_search = request.POST.get(f'columns[{sex_index}][search][value]')
    else:
        sex_search = ''
    # litter_search
    if 'litter_size' in attached_service.pedigree_columns.split(','):
        litter_index = int(attached_service.pedigree_columns.split(',').index('litter_size')) + 1
        try:
            litter_search = int(request.POST.get(f'columns[{litter_index}][search][value]'))
        except ValueError:
            litter_search = ''
    else:
        litter_search = ''
    # parent_father_search
    if 'parent_father' in attached_service.pedigree_columns.split(','):
        father_index = int(attached_service.pedigree_columns.split(',').index('parent_father')) + 1
        father_search = request.POST.get(f'columns[{father_index}][search][value]')
    else:
        father_search = ''
    # parent_father_notes_search
    if 'parent_father_notes' in attached_service.pedigree_columns.split(','):
        father_notes_index = int(attached_service.pedigree_columns.split(',').index('parent_father_notes')) + 1
        father_notes_search = request.POST.get(f'columns[{father_notes_index}][search][value]')
    else:
        father_notes_search = ''
    # parent_mother_search
    if 'parent_mother' in attached_service.pedigree_columns.split(','):
        mother_index = int(attached_service.pedigree_columns.split(',').index('parent_mother')) + 1
        mother_search = request.POST.get(f'columns[{mother_index}][search][value]')
    else:
        mother_search = ''
    # parent_mother_notes_search
    if 'parent_mother_notes' in attached_service.pedigree_columns.split(','):
        mother_notes_index = int(attached_service.pedigree_columns.split(',').index('parent_mother_notes')) + 1
        mother_notes_search = request.POST.get(f'columns[{mother_notes_index}][search][value]')
    else:
        mother_notes_search = ''
    # breed_group_search
    # breed_search
    if 'breed' in attached_service.pedigree_columns.split(','):
        breed_index = int(attached_service.pedigree_columns.split(',').index('breed')) + 1
        breed_search = request.POST.get(f'columns[{breed_index}][search][value]')
    else:
        breed_search = ''
    # coi_search
    # mean_kinship_search

    # desc or asc
    if request.POST.get('order[0][dir]') == 'asc':
        direction = ""
    else:
        direction = "-"
    # sort map
    for data in column_data:
        if sort_by == column_data[data]['db_id']:
            sort_by_col = f"{direction}{column_data[data]['db_id']}"
            break
        else:
            sort_by_col = f"-reg_no"

    # get breeds editable (length is 0 if they're not a breed admin)
    breeds_editable = request.POST.get('breeds-editable').replace('[', '').replace(']', '').replace("&#39;", '').replace("'", '').replace(', ', ',').split(',')
    if '' in breeds_editable:
        breeds_editable.remove('')

    pedigrees = []
    
    # call the function to apply filters and return all pedigrees
    all_pedigrees, total_pedigrees = get_filtered_pedigrees(attached_service, sort_by_col, start, end, 
                    breeder_search=breeder_search, owner_search=owner_search,
                    reg_no_search=reg_no_search, tag_no_search=tag_no_search, name_search=name_search,
                    desc_search=desc_search, dor_search=dor_search, dob_search=dob_search, dod_search=dod_search,
                    status_search=status_search, sex_search=sex_search, litter_search=litter_search,
                    father_search=father_search, father_notes_search=father_notes_search, 
                    mother_search=mother_search, mother_notes_search=mother_notes_search, breed_search=breed_search)

    if all_pedigrees.count() > 0:
        for pedigree in all_pedigrees.all():
            # update pedigree custom fields if they need updating
            update_pedigree_cf(attached_service, pedigree)

            # allow access to pedigree view page, or don't (include disabled if not)
            href = ''
            disabled = ''

            # check whether they have permission to access pedigree view page
            breeder_users = []
            if pedigree.breeder:
                if pedigree.breeder.user:
                    breeder_users.append(pedigree.breeder.user)
            if pedigree.current_owner:
                if pedigree.current_owner.user:
                    breeder_users.append(pedigree.current_owner.user)

            if has_permission(request, {'read_only': 'breeder', 'contrib': True, 'admin': True, 'breed_admin': 'breed'},
                                        pedigrees=[pedigree],
                                        breeder_users=breeder_users):
                href = f"""href='{reverse("pedigree", args=[pedigree.id])}'"""
            else:
                disabled = 'disabled'

            row = {}
            row['action'] = f"""<a {href}><button class='btn btn-info' {disabled}>View</button></a>"""
            for col in columns:
                for data in column_data:
                    if col == column_data[data]['db_id']:
                        try:
                            exec(f"row[column_data[data]['db_id']] = pedigree.{column_data[data]['db_id_internal']}")
                        except AttributeError:
                            row[column_data[data]['db_id']] = ""
                        break
            pedigrees.append(row)
        complete_data = {
            "draw": 0,
            "recordsTotal": all_pedigrees.count(),
              "recordsFiltered": total_pedigrees,
            "data": pedigrees
        }
    else:
        complete_data = {
            "draw": 0,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }
    return HttpResponse(dumps(complete_data))


def get_filtered_pedigrees(attached_service, sort_by_col, start, end,
        search="", breeder_search="", owner_search="", reg_no_search="", tag_no_search="", name_search="", desc_search="", 
        dor_search="", dob_search="", dod_search="", status_search="", sex_search="", litter_search="",
        father_search="", father_notes_search="", mother_search="", mother_notes_search="",
        breed_search=""):
    
    # reg_no, name, litter_size, sale_or_hire - none of these can be None - the rest of the filterable fields can

    # the following functions return the corresponding condition, or no conidition, depending if there is user input

    def breeder_cond():
        if breeder_search:
            return Q(breeder__breeding_prefix__icontains=breeder_search)
        else:
            return Q()

    def owner_cond():
        if owner_search:
            return Q(current_owner__breeding_prefix__icontains=owner_search)
        else:
            return Q()

    def reg_no_cond():
        if reg_no_search:
            return Q(reg_no__icontains=reg_no_search)
        else:
            return Q()

    def tag_no_cond():
        if tag_no_search:
            return Q(tag_no__icontains=tag_no_search)
        else:
            return Q()

    def name_cond():
        if name_search:
            return Q(name__icontains=name_search)
        else:
            return Q()

    def desc_cond():
        if desc_search:
            return Q(description__icontains=desc_search)
        else:
            return Q()

    def dor_cond():
        if dor_search:
            return Q(date_of_registration__icontains=dor_search)
        else:
            return Q()

    def dob_cond():
        if dob_search:
            return Q(dob__icontains=dob_search)
        else:
            return Q()

    def dod_cond():
        if dod_search:
            return Q(dod__icontains=dod_search)
        else:
            return Q()

    def status_cond():
        if status_search:
            return Q(status__icontains=status_search)
        else:
            return Q()

    def sex_cond():
        if sex_search:
            return Q(sex__icontains=sex_search)
        else:
            return Q()

    def litter_cond():
        if litter_search:
            return Q(litter_size__iexact=litter_search)
        else:
            return Q()

    def father_cond():
        if father_search:
            return Q(parent_father__reg_no__icontains=father_search)
        else:
            return Q()

    def father_notes_cond():
        if father_notes_search:
            return Q(parent_father_notes__icontains=father_notes_search)
        else:
            return Q()

    def mother_cond():
        if mother_search:
            return Q(parent_mother__reg_no__icontains=mother_search)
        else:
            return Q()

    def mother_notes_cond():
        if mother_notes_search:
            return Q(parent_mother_notes__icontains=mother_notes_search)
        else:
            return Q()

    def breed_cond():
        if breed_search:
            return Q(breed__breed_name__icontains=breed_search)
        else:
            return Q()

    # filter pedigrees
    if "" == search == breeder_search == owner_search == reg_no_search == tag_no_search == name_search == desc_search\
                == dor_search == dob_search == dod_search == status_search == sex_search == litter_search\
                == father_search == father_notes_search == mother_search == mother_notes_search == breed_search:
        all_pedigrees = Pedigree.objects.filter(account=attached_service).order_by(sort_by_col).distinct()[
                            start:start + end]
    else:
        all_pedigrees = Pedigree.objects.filter(
            Q(reg_no__icontains=search) |
            Q(tag_no__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(date_of_registration__icontains=search) |
            Q(dob__icontains=search) |
            Q(dod__icontains=search) |
            Q(status__icontains=search) |
            Q(sex__icontains=search) |
            Q(litter_size__iexact=litter_search) |
            Q(parent_father__reg_no__icontains=search) |
            Q(parent_father_notes__icontains=search) |
            Q(parent_mother__reg_no__icontains=search) |
            Q(parent_mother_notes__icontains=search) |
            Q(breed_group__icontains=search) |
            Q(breed__breed_name__icontains=search) |
            Q(coi__icontains=search) |
            Q(mean_kinship__icontains=search),
            breeder_cond(),
            owner_cond(),
            reg_no_cond(),
            tag_no_cond(),
            name_cond(),
            desc_cond(),
            dor_cond(),
            dob_cond(),
            dod_cond(),
            status_cond(),
            sex_cond(),
            litter_cond(),
            father_cond(),
            father_notes_cond(),
            mother_cond(),
            mother_notes_cond(),
            breed_cond(),
            account=attached_service).order_by(sort_by_col).distinct()[start:start + end]

    if "" == search == breeder_search == owner_search == reg_no_search == tag_no_search == name_search == desc_search\
                == dor_search == dob_search == dod_search == status_search == sex_search == litter_search\
                == father_search == father_notes_search == mother_search == mother_notes_search == breed_search:
        total_pedigrees = Pedigree.objects.filter(account=attached_service).distinct().count()
    else:
        total_pedigrees = Pedigree.objects.filter(
            Q(reg_no__icontains=search) |
            Q(tag_no__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(date_of_registration__icontains=search) |
            Q(dob__icontains=search) |
            Q(dod__icontains=search) |
            Q(status__icontains=search) |
            Q(sex__icontains=search) |
            Q(litter_size__iexact=litter_search) |
            Q(parent_father__reg_no__icontains=search) |
            Q(parent_father_notes__icontains=search) |
            Q(parent_mother__reg_no__icontains=search) |
            Q(parent_mother_notes__icontains=search) |
            Q(breed_group__icontains=search) |
            Q(breed__breed_name__icontains=search) |
            Q(coi__icontains=search) |
            Q(mean_kinship__icontains=search),
            breeder_cond(),
            owner_cond(),
            reg_no_cond(),
            tag_no_cond(),
            name_cond(),
            desc_cond(),
            dor_cond(),
            dob_cond(),
            dod_cond(),
            status_cond(),
            sex_cond(),
            litter_cond(),
            father_cond(),
            father_notes_cond(),
            mother_cond(),
            mother_notes_cond(),
            breed_cond(),
            account=attached_service).order_by(
            sort_by_col).count()
    
    return all_pedigrees, total_pedigrees


def get_ta_pedigrees(request, sex, state, avoid):
    attached_service = get_main_account(request.user)
    query = request.GET['query']

    # if sex is given, filter for the given sex
    filter_sex = {}
    if sex in ["male", "female", "castrated"]:
        filter_sex = {'sex': sex}

    # if state given, filter for the given state
    filter_state = {}
    if state in ["alive", "dead", "unknown"]:
        filter_state = {'status': state}

    if avoid == "any":
        # don't need to avoid any self pedigrees
        all_peds = Pedigree.objects.filter(Q(reg_no__icontains=query) |
                                       Q(name__icontains=query) |
                                       Q(tag_no__icontains=query),
                                       account=attached_service,
                                       **filter_sex,
                                       **filter_state)[:10]
    else:
        # need to avoid a self pedigree
        all_peds = Pedigree.objects.filter(Q(reg_no__icontains=query) |
                                       Q(name__icontains=query) |
                                       Q(tag_no__icontains=query),
                                       account=attached_service,
                                       **filter_sex,
                                       **filter_state).exclude(id=avoid)[:10]

    data = serialize('json', list(all_peds), fields=('reg_no', 'name', 'tag_no'))
    return HttpResponse(data)

