from django.shortcuts import HttpResponse
from account.views import get_main_account, has_permission
from django.db.models import Q
from .models import BirthNotification
from json import dumps
from django.urls import reverse


def get_birth_notifications_td(request):
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
    if sort_by == 'bn no':
        sort_by_col = f"{direction}bn_number"
    elif sort_by == "date added":
        sort_by_col = f"{direction}date_added"
    else:
        sort_by_col = f"{direction}user"

    births = []
    
    all_births = BirthNotification.objects.filter(
        Q(breeder__breeding_prefix__icontains=search)|
        Q(bn_number__icontains=search)|
        Q(date_added__icontains=search),
        account=attached_service).order_by(sort_by_col).distinct()[start:start + end]
    #.order_by(sort_by_col)
    total_births = BirthNotification.objects.filter(
        Q(breeder__breeding_prefix__icontains=search) |
        Q(bn_number__icontains=search) |
        Q(date_added__icontains=search),
        account=attached_service).order_by(sort_by_col).distinct().count()

    if all_births.count() > 0:
        for birth in all_births:
            # allow access to pedigree view page, or don't (include disabled if not)
            href = ''
            disabled = ''

            row = {}
            try:
                row['breeder'] = birth.breeder.breeding_prefix
            except AttributeError:
                row['breeder'] = ""
            row['births'] = birth.births.all().count()
            row['bn no'] = birth.bn_number
            row['date added'] = birth.date_added.date().strftime("%d %b %Y")
            row['action'] = f"""<a href="/birth_notification/birth_notification/{birth.id}"><button class="btn btn-sm btn-outline-info mr-1">View</button></a></td>"""



            births.append(row)
        complete_data = {
            "draw": 0,
            "recordsTotal": all_births.count(),
            "recordsFiltered": total_births,
            "data": births
        }
    else:
        complete_data = {
            "draw": 0,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }
    from django.core.serializers.json import DjangoJSONEncoder
    return HttpResponse(dumps(complete_data,sort_keys=True,
  indent=1,
  cls=DjangoJSONEncoder))
