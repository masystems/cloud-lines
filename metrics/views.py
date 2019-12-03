from django.shortcuts import render, HttpResponse
from account.views import is_editor, get_main_account
from pedigree.models import Pedigree
from django.core.serializers.json import DjangoJSONEncoder
from json import dumps, loads
import requests


def metrics(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no', 'coi')
    return render(request, 'metrics.html')


def coi(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no', 'parent_father__reg_no', 'parent_mother__reg_no', 'sex', 'breed', 'status')

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/coi/', json=dumps(list(pedigrees), cls=DjangoJSONEncoder))
    coi_dict = loads(coi_raw.json())
    for pedigree in coi_dict:
        Pedigree.objects.filter(account=attached_service, reg_no=pedigree['Indiv']).update(coi=int(pedigree['Inbr'])*100)

    return HttpResponse(coi_dict)