from django.shortcuts import render, HttpResponse, redirect
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
import urllib.parse
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
    attached_service = get_main_account(request.user)
    return render(request, 'reports.html', {'queue_items': ReportQueue.objects.filter(account=attached_service),
                                            'breeds': Breed.objects.filter(account=attached_service)})


@login_required(login_url="/account/login")
def census(request, type):
    attached_service = get_main_account(request.user)
    if type != "form":
        queue_item = ReportQueue.objects.create(account=attached_service,
                                                user=request.user,
                                                file_name="",
                                                file_type=type,
                                                complete=False)
    elif type == "form":
        start_date_object = datetime.strptime(request.POST.get('from_date'), '%d/%m/%Y')
        start_date = start_date_object.strftime('%Y-%m-%d')
        end_date_object = datetime.strptime(request.POST.get('end_date'), '%d/%m/%Y')
        end_date = end_date_object.strftime('%Y-%m-%d')

        if 'xls_submit' in request.POST:
            type = 'xls'
        else:
            type = 'pdf'

        queue_item = ReportQueue.objects.create(account=attached_service,
                                                user=request.user,
                                                from_date=start_date,
                                                to_date=end_date,
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

    data = '{"queue_id": %d, "domain": "%s", "token": "%s"}' % (queue_item.id, domain, token)

    post_res = requests.post(url=f'{settings.ORCH_URL}/api/reports/census/', headers=headers, data=data)

    return redirect('reports')

@login_required(login_url="/account/login")
def census_results_complete(request):
    # get queue item
    stud_item = ReportQueue.objects.filter(id=request.POST.get('item_id'), complete=False)

    if len(stud_item) > 0:
        # process only the first item in the queue list
        item = stud_item[0]
        # check if item is complete
        tld = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/"
        export_file = requests.get(urllib.parse.urljoin(tld, f"reports/{item.file_name}"))
        # set item to complete if it's true
        if export_file.status_code == 200:
            item.complete = True
            item.save()

        return HttpResponse(dumps({'result': 'success',
                                   'complete': item.complete,
                                   'download_url': item.download_url}))
    # queue item not found
    else:
        return HttpResponse(dumps({'result': 'fail'}))

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

    queue_item = ReportQueue.objects.create(account=attached_service,
                                            user=request.user,
                                            file_name="",
                                            file_type="xls",
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

    data = '{"queue_id": %d, "domain": "%s", "token": "%s"}' % (queue_item.id, domain, token)

    post_res = requests.post(url=f'{settings.ORCH_URL}/api/reports/all/', headers=headers, data=data)

    return redirect('reports')


def fangr(request):
     # check if user has permission
    if request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': True}):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()

    attached_service = get_main_account(request.user)

    queue_item = ReportQueue.objects.create(account=attached_service,
                                            user=request.user,
                                            file_name="",
                                            file_type="xls",
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

    data = '{"queue_id": %d, "domain": "%s", "account": %d, "year": "%s", "breed": "%d", "token": "%s"}' % (queue_item.id,
                                                                                                            domain,
                                                                                                            attached_service.id,
                                                                                                            request.POST.get('year'),
                                                                                                            Breed.objects.filter(breed_name__iexact=request.POST.get('breed')).first().id,
                                                                                                            token)

    post_res = requests.post(url=f'{settings.ORCH_URL}/api/reports/fangr/', headers=headers, data=data)

    return redirect('reports')