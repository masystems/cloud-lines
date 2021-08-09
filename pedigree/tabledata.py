from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.db.models import Q
from .models import Pedigree
from account.views import is_editor, get_main_account
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

    # make an int if possible to filter for litter size
    search_int = ''
    try:
        search_int = int(search)
    except ValueError:
        pass

    # get breeds editable (length is 0 if they're not a breed admin)
    breeds_editable = request.POST.get('breeds-editable').replace('[', '').replace(']', '').replace("&#39;", '').replace("'", '').replace(', ', ',').split(',')
    if '' in breeds_editable:
        breeds_editable.remove('')

    pedigrees = []
    if search == "":
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
            Q(litter_size__iexact=search_int) |
            Q(parent_father__reg_no__icontains=search) |
            Q(parent_father_notes__icontains=search) |
            Q(parent_mother__reg_no__icontains=search) |
            Q(parent_mother_notes__icontains=search) |
            Q(breed_group__icontains=search) |
            Q(breed__breed_name__icontains=search) |
            Q(coi__icontains=search) |
            Q(mean_kinship__icontains=search),
            account=attached_service).order_by(sort_by_col).distinct()[start:start + end]
    if search == "":
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
            Q(litter_size__iexact=search_int) |
            Q(parent_father__reg_no__icontains=search) |
            Q(parent_father_notes__icontains=search) |
            Q(parent_mother__reg_no__icontains=search) |
            Q(parent_mother_notes__icontains=search) |
            Q(breed_group__icontains=search) |
            Q(breed__breed_name__icontains=search) |
            Q(coi__icontains=search) |
            Q(mean_kinship__icontains=search),
            account=attached_service).order_by(
            sort_by_col).count()

    if all_pedigrees.count() > 0:
        for pedigree in all_pedigrees.all():
            # update pedigree custom fields if they need updating
            update_pedigree_cf(attached_service, pedigree)

            # allow access to pedigree view page, or don't (include tooltip if not)
            href = ''
            tooltip = ''
            if len(breeds_editable) == 0 or pedigree.breed.breed_name in breeds_editable:
                href = f"""href='{reverse("pedigree", args=[pedigree.id])}'"""
            else:
                tooltip = 'data-toggle="tooltip" data-placement="top" title="You do not have permission to view this pedigree"'

            row = {}
            row['action'] = f"""<a {href}><button class='btn btn-info' {tooltip}>View</button></a>"""
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

