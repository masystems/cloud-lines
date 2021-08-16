from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.db.models import Q
from io import BytesIO
from account.views import is_editor, get_main_account, has_permission, redirect_2_login
from breeder.models import Breeder
from pedigree.models import Pedigree
from xhtml2pdf import pisa
from datetime import datetime
import xlwt

@login_required(login_url="/account/login")
def reports(request):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}, []):
            return redirect_2_login(request)
    else:
        raise PermissionError()
    
    return render(request, 'reports.html')


@login_required(login_url="/account/login")
def census(request, type):
    # check if user has permission
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}, []):
            return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}, []):
            raise PermissionError()
    else:
        raise PermissionError()
    
    attached_service = get_main_account(request.user)
    date = datetime.now()

    form = False
    if type == 'form':
        form = True
        # convert dates
        start_date_object = datetime.strptime(request.POST.get('from_date'), '%d/%m/%Y')
        start_date = start_date_object.strftime('%Y-%m-%d')
        end_date_object = datetime.strptime(request.POST.get('end_date'), '%d/%m/%Y')
        end_date = end_date_object.strftime('%Y-%m-%d')

        if 'xls_submit' in request.POST:
            type = 'xls'
        else:
            type = 'pdf'

    if type == 'xls':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # creating workbook
        workbook = xlwt.Workbook(encoding='utf-8')

        # adding sheet
        worksheet = workbook.add_sheet("flockbook")

        # Sheet header, first row
        row_num = 0

        font_style_header = xlwt.XFStyle()
        # headers are bold
        font_style_header.font.bold = True

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'

        # column header names, you can use your own headers here
        columns = ['Sex', 'Reg No', 'Date Of Birth', 'Name', 'Tag No', 'Litter Size', 'Sire', 'Sire Name', 'Dam', 'Dam Name', 'DOR']

        # write column headers in sheet
        for col_num in range(len(columns)):
            worksheet.write(row_num, col_num, columns[col_num], font_style_header)

        for breeder in Breeder.objects.filter(account=attached_service, active=True):
            # write breeder column headers in sheet
            row_num = row_num + 1
            worksheet.write(row_num, 0, breeder.contact_name, font_style_header)
            worksheet.write(row_num, 1, f"Prefix: {breeder}", font_style_header)

            # Sheet body, remaining rows
            font_style = xlwt.XFStyle()

            if form:
                pedigrees = Pedigree.objects.filter(account=attached_service,
                                                    current_owner=breeder,
                                                    date_of_registration__range=[start_date, end_date],
                                                    status='alive')
            else:
                pedigrees = Pedigree.objects.filter(account=attached_service, current_owner=breeder, status='alive')
            for pedigree in pedigrees:
                row_num = row_num + 1
                try:
                    father = pedigree.parent_father.reg_no
                    father_name = pedigree.parent_father.name
                except AttributeError:
                    father = ""
                    father_name = ""
                try:
                    mother = pedigree.parent_mother.reg_no
                    mother_name = pedigree.parent_mother.name
                except AttributeError:
                    mother = ""
                    mother_name = ""
                worksheet.write(row_num, 0, pedigree.sex, font_style)
                worksheet.write(row_num, 1, pedigree.reg_no, font_style)
                worksheet.write(row_num, 2, pedigree.dob, font_style)
                worksheet.write(row_num, 3, pedigree.name, font_style)
                worksheet.write(row_num, 4, pedigree.tag_no, font_style)
                worksheet.write(row_num, 5, pedigree.litter_size, font_style)
                worksheet.write(row_num, 6, father, font_style)
                worksheet.write(row_num, 7, father_name, font_style)
                worksheet.write(row_num, 8, mother, font_style)
                worksheet.write(row_num, 9, mother_name, font_style)
                worksheet.write(row_num, 10, pedigree.date_of_registration, date_format)
        workbook.save(response)
    elif type == 'pdf':
        context = {}
        attached_service = get_main_account(request.user)
        context['breeders'] = Breeder.objects.filter(account=attached_service, active=True)
        if form:
            context['pedigrees'] = Pedigree.objects.filter(account=attached_service,
                                                           status='alive',
                                                           date_of_registration__range=[start_date, end_date],)
        else:
            context['pedigrees'] = Pedigree.objects.filter(account=attached_service, status='alive')

        pdf = render_to_pdf('census.html', context)
        response = HttpResponse(pdf, content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="{attached_service.animal_type}-Export-{date.strftime("%Y-%m-%d")}.{type}"'
    return response


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

        for pedigree in Pedigree.objects.filter(account=attached_service, status__icontains='alive'):
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