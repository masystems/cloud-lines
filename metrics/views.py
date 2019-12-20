from django.shortcuts import render, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from account.views import is_editor, get_main_account
from pedigree.models import Pedigree
from django.core.serializers.json import DjangoJSONEncoder
from .models import CoiLastRun, MeanKinshipLastRun
from json import dumps, loads
from threading import Thread
from datetime import datetime, timedelta
import requests


def metrics(request):
    attached_service = get_main_account(request.user)

    try:
        obj = CoiLastRun.objects.get(account=attached_service)
        obj.last_run += timedelta(minutes=attached_service.coi_timeout)
        coi_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    except ObjectDoesNotExist:
        date = datetime.now()
        coi_date = date.strftime("%b %d, %Y %H:%M:%S")

    try:
        obj = MeanKinshipLastRun.objects.get(account=attached_service)
        obj.last_run += timedelta(minutes=attached_service.coi_timeout)
        mean_kinship_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    except ObjectDoesNotExist:
        date = datetime.now()
        mean_kinship_date = date.strftime("%b %d, %Y %H:%M:%S")

    return render(request, 'metrics.html', {'pedigrees': Pedigree.objects.filter(account=attached_service),
                                            'coi_date': coi_date,
                                            'mean_kinship_date': mean_kinship_date})


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
                                                                         'breed__breed_name',
                                                                         'status')

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/coi/',
                            json=dumps(list(pedigrees), cls=DjangoJSONEncoder))
    coi_dict = loads(coi_raw.json())
    for pedigree in coi_dict:
        Pedigree.objects.filter(account=attached_service, reg_no=pedigree['Indiv']).update(coi=pedigree['Inbr'])

    return HttpResponse(coi_dict)


def kinship(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service, status='alive').values('reg_no',
                                                                                         'parent_father__reg_no',
                                                                                         'parent_mother__reg_no',
                                                                                         'sex',
                                                                                         'breed__breed_name',
                                                                                         'status')
    data = list(pedigrees)
    mother = request.POST['mother']
    father = request.POST['father']

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/{}/{}/kinship/'.format(mother, father),
                            json=dumps(data, cls=DjangoJSONEncoder))
    print(coi_raw.status_code)
    return HttpResponse(coi_raw.json())


def run_mean_kinship(request):
    attached_service = get_main_account(request.user)
    obj, created = MeanKinshipLastRun.objects.get_or_create(account=attached_service)

    obj.last_run = datetime.now()
    obj.save()
    Thread(target=mean_kinship, args=(request,))
    obj.last_run += timedelta(minutes=attached_service.mean_kinship_timeout)
    mean_kinship_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    return HttpResponse(dumps({'mean_kinship_date': mean_kinship_date}))


def mean_kinship(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service, status='alive').values('reg_no',
                                                                                         'parent_father__reg_no',
                                                                                         'parent_mother__reg_no',
                                                                                         'sex',
                                                                                         'breed__breed_name',
                                                                                         'status')

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/mean_kinship/',
                            json=dumps(list(pedigrees), cls=DjangoJSONEncoder), stream=True)

    coi_dict = loads(coi_raw.json())
    for pedigree, value in coi_dict.items():
        Pedigree.objects.filter(account=attached_service, reg_no=pedigree.replace('.', '-')).update(mean_kinship=value['1'])

    return HttpResponse(coi_raw.json())


def stud_advisor_mother_details(request):
    attached_service = get_main_account(request.user)
    cois = Pedigree.objects.filter(account=attached_service).values('coi')
    total = 0
    for coi in cois.all():
        total += coi['coi']
    breed_mean_coi = total / Pedigree.objects.filter(account=attached_service).count()
    mother = Pedigree.objects.get(account=attached_service, reg_no=request.POST['mother'])
    mother_details = {'reg_no': mother.reg_no,
                      'mk': str(mother.mean_kinship),
                      'band': get_band(mother),
                      'breed_mean_coi': str(breed_mean_coi)}
    return HttpResponse(dumps(mother_details))


def stud_advisor(request):
    group_letters = ['A', 'B', 'C', 'D', 'E', 'F']
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service, status='alive').values('reg_no',
                                                                                         'parent_father__reg_no',
                                                                                         'parent_mother__reg_no',
                                                                                         'sex',
                                                                                         'breed__breed_name',
                                                                                         'status')

    mother = request.POST['mother']

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/{}/stud_advisor/'.format(mother),
                            json=dumps(list(pedigrees), cls=DjangoJSONEncoder), stream=True)

    mother = Pedigree.objects.get(account=attached_service, reg_no=mother)
    mother_band = get_band(mother)

    studs_raw = loads(coi_raw.json())
    studs_data = {}
    for stud, kinship in studs_raw.items():
        male = Pedigree.objects.get(account=attached_service, reg_no=stud)
        stud_band = get_band(male)
        if stud_band == mother_band or \
                group_letters.index(mother_band) == group_letters.index(stud_band)-1 or \
                group_letters.index(mother_band) == group_letters.index(stud_band)+1:
            studs_data[stud] = {'id': male.id,
                                'reg_no': male.reg_no,
                                'name': male.name,
                                'kinship': kinship,
                                'kinship_band': stud_band}

    return HttpResponse(dumps(studs_data))


def get_band(pedigree):
    if pedigree.mean_kinship < pedigree.breed.mk_a:
        return 'A'
    elif pedigree.breed.mk_a <= pedigree.mean_kinship < pedigree.breed.mk_b:
        return 'B'
    elif pedigree.breed.mk_b <= pedigree.mean_kinship < pedigree.breed.mk_c:
        return 'C'
    elif pedigree.breed.mk_c <= pedigree.mean_kinship < pedigree.breed.mk_d:
        return 'D'
    else:
        return 'E'
