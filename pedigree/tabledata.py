from django.shortcuts import HttpResponse, reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Pedigree
from account.views import is_editor, get_main_account
from .functions import get_site_pedigree_column_headings
from json import dumps, loads, JSONDecodeError
from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_pedigrees(request):
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
    # if sort_by == "id":
    #     sort_by_col = f"{direction}membership_number"
    # elif sort_by == "name":
    #     sort_by_col = f"{direction}member__user_account__first_name"
    # elif sort_by == "email":
    #     sort_by_col = f"{direction}member__user_account__email"
    # elif sort_by == "address":
    #     sort_by_col = f"{direction}member__address_line_1"
    # elif sort_by == "contact":
    #     sort_by_col = f"{direction}member__contact_number"
    # elif sort_by == "membership_type":
    #     sort_by_col = f"{direction}price"
    # elif sort_by == "membership_status":
    #     sort_by_col = f"{direction}active"
    # elif sort_by == "payment_method":
    #     sort_by_col = f"{direction}payment_method__payment_name"
    # elif sort_by == "billing_interval":
    #     sort_by_col = f"{direction}price__interval"
    # elif sort_by == "comments":
    #     sort_by_col = f"{direction}comments"
    # elif sort_by == "gift_aid":
    #     sort_by_col = f"{direction}gift_aid"
    # elif sort_by == "membership_start":
    #     sort_by_col = f"{direction}membership_start"
    # elif sort_by == "membership_expiry":
    #     sort_by_col = f"{direction}membership_expiry"
    # else:
    sort_by_col = f"-reg_no"

    pedigrees = []
    if search == "":
        all_pedigrees = Pedigree.objects.filter(account=attached_service).order_by(sort_by_col).distinct()[
                            start:start + end]
    else:
        all_pedigrees = Pedigree.objects.filter(
            # Q(member__user_account__first_name__icontains=search) |
            # Q(member__user_account__last_name__icontains=search) |
            # Q(member__user_account__email__icontains=search) |
            # Q(member__address_line_1__icontains=search) |
            # Q(member__address_line_2__icontains=search) |
            # Q(member__town__icontains=search) |
            # Q(member__county__icontains=search) |
            # Q(member__country__icontains=search) |
            # Q(member__postcode__icontains=search) |
            # Q(member__contact_number__icontains=search) |
            # Q(membership_number__icontains=search) |
            # Q(price__nickname__icontains=search) |
            # Q(custom_fields__icontains=search),
            account=attached_service).order_by(sort_by_col).distinct()[start:start + end]
    if search == "":
        total_pedigrees = Pedigree.objects.filter(account=attached_service).distinct().count()
    else:
        total_pedigrees = Pedigree.objects.filter(
            # Q(member__user_account__first_name__icontains=search) |
            #                                                   Q(member__user_account__last_name__icontains=search) |
            #                                                   Q(member__user_account__email__icontains=search) |
            #                                                   Q(member__address_line_1__icontains=search) |
            #                                                   Q(member__address_line_2__icontains=search) |
            #                                                   Q(member__town__icontains=search) |
            #                                                   Q(member__county__icontains=search) |
            #                                                   Q(member__country__icontains=search) |
            #                                                   Q(member__postcode__icontains=search) |
            #                                                   Q(member__contact_number__icontains=search) |
            #                                                   Q(membership_number__icontains=search) |
            #                                                   Q(custom_fields__icontains=search),
                                                              account=attached_service).order_by(
            sort_by_col).count()

    if all_pedigrees.count() > 0:
        columns, column_data = get_site_pedigree_column_headings(attached_service)
        #print(columns)
        for pedigree in all_pedigrees.all():
            row = {}
            for col in columns:
                for data in column_data:
                    print(col, column_data[data]['db_id'])
                    if col == column_data[data]['db_id']:
                        # print(pedigree.exec("column_data[data]['db_id_internal']"))
                        try:
                            exec(f"row[column_data[data]['db_id']] = pedigree.{column_data[data]['db_id_internal']}")
                        except AttributeError:
                            row[column_data[data]['db_id']] = ""
                        break
            pedigrees.append(row)
            print(row)
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
