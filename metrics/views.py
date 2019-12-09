from django.shortcuts import render, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from account.views import is_editor, get_main_account
from pedigree.models import Pedigree
from django.core.serializers.json import DjangoJSONEncoder
from .models import CoiLastRun
from json import dumps, loads
from threading import Thread
from datetime import datetime, timedelta
import requests


def metrics(request):
    attached_service = get_main_account(request.user)
    # Jan 5, 2021 15:37:25
    # now = datetime.now() + timedelta(seconds=10)
    # date = now.strftime("%b %d, %Y %H:%M:%S")
    try:
        obj = CoiLastRun.objects.get(account=attached_service)
        obj.last_run += timedelta(minutes=attached_service.coi_timeout)
        coi_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    except ObjectDoesNotExist:
        date = datetime.now()
        coi_date = date.strftime("%b %d, %Y %H:%M:%S")


    return render(request, 'metrics.html', {'pedigrees': Pedigree.objects.filter(account=attached_service),
                                            'coi_date': coi_date})


def run_coi(request):
    attached_service = get_main_account(request.user)
    obj, created = CoiLastRun.objects.get_or_create(account=attached_service)
    obj.last_run = datetime.now()
    obj.save()
    Thread(target=coi, args=(request,))
    obj.last_run += timedelta(minutes=attached_service.coi_timeout)
    coi_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    return HttpResponse(dumps({'coi_date': coi_date}))


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
                            json=dumps(data, cls=DjangoJSONEncoder))

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