from django.shortcuts import HttpResponse
from django.db.models import Q
from pedigree.models import Pedigree
from account.views import get_main_account
from pedigree.functions import get_site_pedigree_column_headings
from json import dumps

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
    
    pedigrees = [
        {'breeder__breeding_prefix': 'breeder__breeding_prefix',
        'current_owner__breeding_prefix': 'current_owner__breeding_prefix',
        'reg_no': 'reg_no',
        'name': 'name'},
        {'breeder__breeding_prefix': 'breeder__breeding_prefix2',
        'current_owner__breeding_prefix': 'current_owner__breeding_prefix2',
        'reg_no': 'reg_no2',
        'name': 'name2'},
    ]

    pedigrees = []
    all_pedigrees = Pedigree.objects.filter(Q(breeder__breeding_prefix__icontains=search)|
                    Q(current_owner__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service).order_by(sort_by_col).distinct()[start:start + end]
    
    total_pedigrees = Pedigree.objects.filter(Q(breeder__breeding_prefix__icontains=search)|
                    Q(current_owner__breeding_prefix__icontains=search)|
                    Q(reg_no__icontains=search)|
                    Q(name=search),
                    account=attached_service).distinct().count()

    if all_pedigrees.count() > 0:
        for pedigree in all_pedigrees:
            row = {}
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
            "recordsTotal": 12,#all_pedigrees.count(),
            "recordsFiltered": 13,#total_pedigrees,
            "data": pedigrees
        }
    return HttpResponse(dumps(complete_data))