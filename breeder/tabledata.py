from django.shortcuts import HttpResponse
from django.db.models import Q
from pedigree.models import Pedigree
from breed_group.models import BreedGroup
from .models import Breeder
from account.views import get_main_account, has_permission
from pedigree.functions import get_site_pedigree_column_headings
from json import dumps
from django.urls import reverse

def get_pedigrees_owned(request):
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

    owner = Breeder.objects.get(id=request.POST.get('owner'))

    pedigrees = []
    
    all_pedigrees = Pedigree.objects.filter(Q(breeder__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service,
                    current_owner=owner).order_by(sort_by_col).distinct()[start:start + end]
    
    total_pedigrees = Pedigree.objects.filter(Q(breeder__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service,
                    current_owner=owner).distinct().count()

    if all_pedigrees.count() > 0:
        for pedigree in all_pedigrees:
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
    return HttpResponse(dumps(complete_data))


def get_pedigrees_bred(request):
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
    
    breeder = Breeder.objects.get(id=request.POST.get('breeder'))

    pedigrees = []
    
    all_pedigrees = Pedigree.objects.filter(Q(current_owner__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service,
                    breeder=breeder).order_by(sort_by_col).distinct()[start:start + end]
    
    total_pedigrees = Pedigree.objects.filter(Q(breeder__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service,
                    breeder=breeder).distinct().count()

    if all_pedigrees.count() > 0:
        for pedigree in all_pedigrees:
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
    
    return HttpResponse(dumps(complete_data))

def get_groups_bred(request):
    attached_service = get_main_account(request.user)
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
    for col in ('group_name', 'breed'):
        if sort_by == col:
            sort_by_col = f"{direction}{col}"
            break
        else:
            sort_by_col = f"-group_name"
    
    breeder = Breeder.objects.get(id=request.POST.get('breeder'))

    groups = []
    
    all_groups = BreedGroup.objects.filter(Q(group_name__icontains=search)|
                    Q(breed__breed_name__icontains=search),
                    account=attached_service,
                    breeder=breeder).order_by(sort_by_col).distinct()[start:start + end]
    
    total_groups = BreedGroup.objects.filter(Q(group_name__icontains=search)|
                    Q(breed__breed_name__icontains=search),
                    account=attached_service,
                    breeder=breeder).distinct().count()

    if all_groups.count() > 0:
        for group in all_groups:
            # allow access to pedigree view page, or don't (include disabled if not)
            href = ''
            disabled = ''

            if has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': 'breed'},
                                        pedigrees=[group]):
                href = f"""href='{reverse("edit_breed_group_form", args=[group.id])}'"""
            else:
                disabled = 'disabled'
            
            row = {}
            row['action'] = f"""<a {href}><button class='btn btn-info' {disabled}>Edit</button></a>"""
            row['group_name'] = group.group_name
            row['breed'] = group.breed.breed_name
            row['male'] = ''
            for member in group.group_members.all():
                if member.sex == 'male':
                    row['male'] = f"""
                        {row['male']}
                        <span class="mytooltip tooltip-effect-4">
                            <span class="tooltip-item">
                                <i class="fad fa-mars"></i> 
                                {member.name}
                            </span>
                            <span class="tooltip-content clearfix">
                                <span class="tooltip-text2">
                                    <a href='{reverse("pedigree", args=[member.id])}' class="btn btn-outline-primary waves-effect waves-light mt-1 ml-1" role="button"><span class="btn-label"><i class="fad fa-mars"></i></span> <strong>Profile</strong></a>
                                    <ul class="list-icons">
                                        <li class="text-muted"><i class="ti-angle-right"></i> <strong>Reg #:</strong> {member.reg_no }</li>
                                        <li class="text-muted"><i class="ti-angle-right"></i> <strong>Name:</strong> {member.name}</li>
                                    </ul>
                                </span>
                            </span>
                        </span>
                    """
            row['female'] = ''
            for member in group.group_members.all():
                if member.sex == 'female':
                    row['female'] = f"""
                        {row['female']}
                        <span class="mytooltip tooltip-effect-4">
                            <span class="tooltip-item">
                                <i class="fad fa-venus"></i> 
                                {member.name}
                            </span>
                            <span class="tooltip-content clearfix">
                                <span class="tooltip-text2">
                                    <a href='{reverse("pedigree", args=[member.id])}' class="btn btn-outline-primary waves-effect waves-light mt-1 ml-1" role="button"><span class="btn-label"><i class="fad fa-venus"></i></span> <strong>Profile</strong></a>
                                    <ul class="list-icons">
                                        <li class="text-muted"><i class="ti-angle-right"></i> <strong>Reg #:</strong> {member.reg_no }</li>
                                        <li class="text-muted"><i class="ti-angle-right"></i> <strong>Name:</strong> {member.name}</li>
                                    </ul>
                                </span>
                            </span>
                        </span> | 
                    """
            groups.append(row)
    
    
    complete_data = {
        "draw": 0,
        "recordsTotal": all_groups.count(),
        "recordsFiltered": total_groups,
        "data": groups
    }
    
    return HttpResponse(dumps(complete_data))