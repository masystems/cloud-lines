from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from account.views import is_editor, get_main_account
from breeder.models import Breeder
from pedigree.models import Pedigree
from datetime import datetime
import xlwt

@login_required(login_url="/account/login")
def reports(request):
    attached_service = get_main_account(request.user)

    return render(request, 'reports.html', {'breeds': 'breeds',})


@login_required(login_url="/account/login")
def flockbook(request):
    attached_service = get_main_account(request.user)
    date = datetime.now()
    response = HttpResponse(content_type='application/ms-excel')
    response[
        'Content-Disposition'] = f'attachment; filename="{attached_service.animal_type}-Export-{date.strftime("%Y-%m-%d")}.xlsx"'
    # creating workbook
    workbook = xlwt.Workbook(encoding='utf-8')

    # adding sheet
    worksheet = workbook.add_sheet("flockbook")

    # Sheet header, first row
    row_num = 0

    font_style_header = xlwt.XFStyle()
    # headers are bold
    font_style_header.font.bold = True

    # column header names, you can use your own headers here
    columns = ['Sex', 'Reg No', 'Date Of Birth', 'Name', 'Tag No', 'Born', 'Sire', 'Damn']

    # write column headers in sheet
    for col_num in range(len(columns)):
        worksheet.write(row_num, col_num, columns[col_num], font_style_header)

    for breeder in Breeder.objects.filter(active=True):
        # write breeder column headers in sheet
        row_num = row_num + 1
        worksheet.write(row_num, 0, breeder.contact_name, font_style_header)
        worksheet.write(row_num, 1, f"Prefix: {breeder}", font_style_header)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        pedigrees = Pedigree.objects.filter(breeder=breeder)
        for pedigree in pedigrees:
            row_num = row_num + 1
            try:
                father = pedigree.parent_father.reg_no
            except AttributeError:
                father = ""
            try:
                mother = pedigree.parent_mother.reg_no
            except AttributeError:
                mother = ""
            worksheet.write(row_num, 0, pedigree.sex, font_style)
            worksheet.write(row_num, 1, pedigree.reg_no, font_style)
            worksheet.write(row_num, 2, pedigree.dob, font_style)
            worksheet.write(row_num, 3, pedigree.name, font_style)
            worksheet.write(row_num, 4, pedigree.tag_no, font_style)
            worksheet.write(row_num, 5, pedigree.born_as, font_style)
            worksheet.write(row_num, 6, father, font_style)
            worksheet.write(row_num, 7, mother, font_style)
    workbook.save(response)
    return response