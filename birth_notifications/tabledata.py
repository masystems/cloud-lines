from django.shortcuts import HttpResponse
from account.views import get_main_account, has_permission
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
    #sort_by_col = f"-reg_no"

    births = []
    
    all_births = BirthNotification.objects.filter(
        account=attached_service).distinct()[start:start + end]
    
    total_births = BirthNotification.objects.filter(
                    account=attached_service).distinct().count()

    if all_births.count() > 0:
        for birth in all_births:
            # allow access to pedigree view page, or don't (include disabled if not)
            href = ''
            disabled = ''

            row = {}
            row['user'] = birth.user.get_full_name()
            row['births'] = birth.births.all().count()
            row['bn no'] = birth.bn_number
            row['date added'] = birth.date_added.isoformat()
            row['action'] = birth.user.get_full_name()


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
