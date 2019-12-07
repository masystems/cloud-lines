from django.shortcuts import render, HttpResponse
from account.views import is_editor, get_main_account
from pedigree.models import Pedigree
from django.core.serializers.json import DjangoJSONEncoder
from json import dumps, loads
import requests


def metrics(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no', 'coi')
    return render(request, 'metrics.html', {'pedigrees': Pedigree.objects.filter(account=attached_service)})


def coi(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no',
                                                                         'parent_father__reg_no',
                                                                         'parent_mother__reg_no',
                                                                         'sex',
                                                                         'breed',
                                                                         'status')

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/coi/',
                            json=dumps(list(pedigrees), cls=DjangoJSONEncoder))
    coi_dict = loads(coi_raw.json())
    for pedigree in coi_dict:
        Pedigree.objects.filter(account=attached_service, reg_no=pedigree['Indiv']).update(coi=pedigree['Inbr'])

    return HttpResponse(coi_dict)


def kinship(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no',
                                                                         'parent_father__reg_no',
                                                                         'parent_mother__reg_no',
                                                                         'sex',
                                                                         'breed',
                                                                         'status')
    data = list(pedigrees)
    mother = request.POST['mother']
    father = request.POST['father']

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/{}/{}/kinship/'.format(mother, father),
                            json=dumps(data, cls=DjangoJSONEncoder), stream=True)

    return HttpResponse(coi_raw.json())


def mean_kinship(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('reg_no',
                                                                         'parent_father__reg_no',
                                                                         'parent_mother__reg_no',
                                                                         'sex',
                                                                         'breed',
                                                                         'status')

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/mean_kinship/',
                            json=dumps(list(pedigrees), cls=DjangoJSONEncoder), stream=True)

    coi_dict = loads(coi_raw.json())
    for pedigree, value in coi_dict.items():
        Pedigree.objects.filter(account=attached_service, reg_no=pedigree.replace('.', '-')).update(mean_kinship=value['1'])

    return HttpResponse(coi_raw.json())