from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.core.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from django.conf import settings
from io import BytesIO
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from pedigree.models import Pedigree
from breed.models import Breed
from .models import ReportQueue
from xhtml2pdf import pisa
from datetime import datetime
from json import dumps
import xlwt
import requests


@login_required(login_url="/account/login")
def reports(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()
    
    return render(request, 'reports.html')


@login_required(login_url="/account/login")
def census(request, type):
    attached_service = get_main_account(request.user)
    queue_item = ReportQueue.objects.create(account=attached_service,
                                            user=request.user,
                                            file_name="",
                                            file_type=type,
                                            complete=False)

    token_res = requests.post(url=f'{settings.ORCH_URL}/api-token-auth/',
                              data={'username': settings.ORCH_USER, 'password': settings.ORCH_PASS})
    ## create header
    headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}
    ## get pedigrees
    if attached_service.domain:
        domain = attached_service.domain
    else:
        domain = "https://cloud-lines.com"

    token, created = Token.objects.get_or_create(user=request.user)

    # queue_item.id
    data = '{"queue_id": %d, "domain": "%s", "token": "%s"}' % (7, domain, token)

    post_res = requests.post(url=f'{settings.ORCH_URL}/api/reports/census/', headers=headers, data=data)

    return HttpResponse(dumps(post_res.json()))


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@login_required(login_url="/account/login")
def all(request, type):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()
    
    attached_service = get_main_account(request.user)

    if type == 'form':
        if 'xls_submit' in request.POST:
            type = 'xls'
        else:
            type = 'pdf'

    if type == 'xls':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # creating workbook
        workbook = xlwt.Workbook(encoding='utf-8')

        # adding sheet
        worksheet = workbook.add_sheet("all living animals")

        # Sheet header, first row
        row_num = 0

        font_style_header = xlwt.XFStyle()
        # headers are bold
        font_style_header.font.bold = True

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'

        # column header names, you can use your own headers here
        columns = ['Breeder',
                   'Current Owner',
                   'Reg No',
                   'Tag No',
                   'Name',
                   'Description',
                   'Date Of Registration',
                   'Date Of Birth',
                   'Sex',
                   'Litter Size',
                   attached_service.father_title,
                   f'{attached_service.father_title} Notes',
                   attached_service.mother_title,
                   f'{attached_service.mother_title} Notes',
                   'Breed',
                   'COI',
                   'Mean Kinship']

        # write column headers in sheet
        for col_num in range(len(columns)):
            worksheet.write(row_num, col_num, columns[col_num], font_style_header)

        # get breeds editable if user is breed admin
        if Breed.objects.filter(account=attached_service, breed_admins__in=[request.user]).exists():
            breeds = Breed.objects.filter(account=attached_service, breed_admins__in=[request.user])
        else:
            breeds = Breed.objects.filter(account=attached_service)

        for pedigree in Pedigree.objects.filter(account=attached_service, status__icontains='alive', breed__in=breeds):
            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            row_num = row_num + 1
            try:
                breeding_prefix = pedigree.breeder.breeding_prefix
            except AttributeError:
                breeding_prefix = ""
            try:
                current_owner = pedigree.current_owner.breeding_prefix
            except AttributeError:
                current_owner = ""
            try:
                father = pedigree.parent_father.reg_no
            except AttributeError:
                father = ""
            try:
                mother = pedigree.parent_mother.reg_no
            except AttributeError:
                mother = ""
            worksheet.write(row_num, 0, breeding_prefix, font_style)
            worksheet.write(row_num, 1, current_owner, font_style)
            worksheet.write(row_num, 2, pedigree.reg_no, font_style)
            worksheet.write(row_num, 3, pedigree.tag_no, font_style)
            worksheet.write(row_num, 4, pedigree.name, font_style)
            worksheet.write(row_num, 5, pedigree.description, font_style)
            worksheet.write(row_num, 6, pedigree.date_of_registration, date_format)
            worksheet.write(row_num, 7, pedigree.dob, date_format)
            worksheet.write(row_num, 8, pedigree.sex, font_style)
            worksheet.write(row_num, 9, pedigree.litter_size, font_style)
            worksheet.write(row_num, 10, father, font_style)
            worksheet.write(row_num, 11, pedigree.parent_father_notes, font_style)
            worksheet.write(row_num, 12, mother, font_style)
            worksheet.write(row_num, 13, pedigree.parent_mother_notes, font_style)
            worksheet.write(row_num, 14, pedigree.breed.breed_name, font_style)
            worksheet.write(row_num, 15, pedigree.coi, font_style)
            worksheet.write(row_num, 16, pedigree.mean_kinship, font_style)
        workbook.save(response)
    date = datetime.now()
    response['Content-Disposition'] = f'attachment; filename="{attached_service.animal_type}-Living_Animal_Export-{date.strftime("%Y-%m-%d")}.{type}"'
    return response