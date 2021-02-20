from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from io import BytesIO
from account.views import is_editor, get_main_account
from breeder.models import Breeder
from pedigree.models import Pedigree
from xhtml2pdf import pisa
from datetime import datetime
import xlwt

@login_required(login_url="/account/login")
def reports(request):
    return render(request, 'reports.html')


@login_required(login_url="/account/login")
def census(request, type):
    attached_service = get_main_account(request.user)
    date = datetime.now()
    if type == 'xlsx':
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

        # column header names, you can use your own headers here
        columns = ['Sex', 'Reg No', 'Date Of Birth', 'Name', 'Tag No', 'Born', 'Sire', 'Damn']

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

            pedigrees = Pedigree.objects.filter(account=attached_service, current_owner=breeder, status='alive')
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
    elif type == 'pdf':
        context = {}
        attached_service = get_main_account(request.user)
        context['breeders'] = Breeder.objects.filter(account=attached_service, active=True)
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


# class GeneratePDF(View):
#     def get(self, request, *args, **kwargs):
#         context = {}
#         context['attached_service'] = get_main_account(request.user)
#         context['lvl1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], id=self.kwargs['pedigree_id'])
#         context = generate_hirearchy(context)
#
#         pdf_filename = "{date}-{name}{pedigree}-certificate".format(
#             date=context['lvl1'].date_added.strftime('%Y-%m-%d'),
#             name=slugify(context['lvl1'].name),
#             pedigree=context['lvl1'].reg_no,
#         )
#
#         pdf = render_to_pdf('certificate.html', context)
#         if pdf:
#             response = HttpResponse(pdf, content_type='application/pdf')
#             filename = "%s.pdf" % pdf_filename
#             content = "attachment; filename=%s" % filename
#             download = request.GET.get("download")
#             if download:
#                 content = "attachment; filename=%s" % filename
#             response['Content-Disposition'] = content
#             return response
#         return HttpResponse("Not found")