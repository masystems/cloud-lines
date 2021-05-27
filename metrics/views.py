from django.shortcuts import render, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from account.views import is_editor, get_main_account
from pedigree.models import Pedigree
from breed.models import Breed
from django.core.serializers.json import DjangoJSONEncoder
from .models import CoiLastRun, MeanKinshipLastRun, StudAdvisorQueue, KinshipQueue
from json import dumps, loads, load
from datetime import datetime, timedelta
import logging
import requests
import pytz
import boto3
import urllib.parse
import urllib.request
from time import time
from boto3.s3.transfer import TransferConfig
from threading import Thread
from itertools import chain


logger = logging.getLogger(__name__)


def calc_last_run(attached_service, obj, dt=None, timezone="UTC"):

    if dt is None:
        dt = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)

    if timezone_aware_date.tzinfo._dst.seconds != 0:
        obj.last_run += timedelta(minutes=attached_service.coi_timeout)
    else:
        obj.last_run += timedelta(minutes=attached_service.coi_timeout * 2)
    return obj.last_run


def metrics(request):
    attached_service = get_main_account(request.user)

    try:
        obj = CoiLastRun.objects.get(account=attached_service)

        obj.last_run = calc_last_run(attached_service, obj)
        coi_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    except ObjectDoesNotExist:
        date = datetime.now()
        coi_date = date.strftime("%b %d, %Y %H:%M:%S")

    try:
        obj = MeanKinshipLastRun.objects.get(account=attached_service)
        obj.last_run = calc_last_run(attached_service, obj)
        mean_kinship_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    except ObjectDoesNotExist:
        date = datetime.now()
        mean_kinship_date = date.strftime("%b %d, %Y %H:%M:%S")

    # queue
    sa_queue = StudAdvisorQueue.objects.filter(account=attached_service)
    k_queue = KinshipQueue.objects.filter(account=attached_service)
    tld = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/"

    queue_items = sorted(
        chain(sa_queue, k_queue),
        key=lambda instance: instance.created)
    for item in queue_items:
        if not item.complete:
            results_file = requests.get(urllib.parse.urljoin(tld, f"metrics/results-{item.file}"))
            if results_file.status_code == 200:
                item.complete = True
                item.save()

    return render(request, 'metrics.html', {'pedigrees': Pedigree.objects.filter(account=attached_service),
                                            'coi_date': coi_date,
                                            'mean_kinship_date': mean_kinship_date,
                                            'breeds': Breed.objects.filter(account=attached_service),
                                            'queue_items': queue_items})


def multi_part_upload_with_s3(file_path, key_path):
    s3 = boto3.resource('s3')
    # Multipart upload
    config = TransferConfig(multipart_threshold=1024 * 10, max_concurrency=10,
                            multipart_chunksize=1024 * 10, use_threads=True)
    s3.meta.client.upload_file(file_path, settings.AWS_S3_CUSTOM_DOMAIN, key_path,
                            ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/json'},
                            Config=config,
                            )


def run_coi(request):
    attached_service = get_main_account(request.user)
    obj, created = CoiLastRun.objects.get_or_create(account=attached_service)
    obj.last_run = datetime.now()
    obj.save()

    coi(request)

    obj.last_run = calc_last_run(attached_service, obj)

    coi_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")

    return HttpResponse(dumps({'coi_date': coi_date}))


def coi(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service).values('id',
                                                                         'parent_father__id',
                                                                         'parent_mother__id',
                                                                         'sex',
                                                                         'breed__breed_name',
                                                                         'status')

    # create unique paths
    if attached_service.service.service_name in ('Small Society', 'Large Society', 'Organisation'):
        host = attached_service.domain.partition('://')[2]
        subdomain = host.partition('.')[0]
        local_output = f"/tmp/coi_{subdomain}_output.json"
        remote_output = f"metrics/coi_{subdomain}_output.json"
        file_name = f"coi_{subdomain}_output.json"
    else:
        local_output = f"/tmp/coi_{attached_service.id}_output.json"
        remote_output = f"metrics/coi_{attached_service.id}_output.json"
        file_name = f"coi_{attached_service.id}_output.json"

    with open(local_output, 'w') as file:
        file.write(dumps(list(pedigrees)))

    multi_part_upload_with_s3(local_output, remote_output)

    data = {'data_path': remote_output,
            'file_name': file_name,
            'domain': attached_service.domain}

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/coi/',
                            json=dumps(data, cls=DjangoJSONEncoder))

    #coi_dict = loads(coi_raw.json())


def kinship(request):
    attached_service = get_main_account(request.user)
    epoch = int(time())

    pedigrees = Pedigree.objects.filter(account=attached_service).values('id',
                                                                         'parent_father__id',
                                                                         'parent_mother__id',
                                                                         'sex',
                                                                         'breed__breed_name',
                                                                         'status')

    try:
        mother = Pedigree.objects.get(reg_no=request.POST['mother'])
    except Pedigree.DoesNotExist:
        response = {'status': 'error',
                    'msg': f"Mother ({request.POST['mother']}) does not exist!"
                    }
        return HttpResponse(dumps(response))
    try:
        father = Pedigree.objects.get(reg_no=request.POST['father'])
    except Pedigree.DoesNotExist:
        response = {'status': 'error',
                    'msg': f"Mother ({request.POST['mother']}) does not exist!"
                    }
        return HttpResponse(dumps(response))

    if attached_service.service.service_name in ('Small Society', 'Large Society', 'Organisation'):
        host = attached_service.domain.partition('://')[2]
        subdomain = host.partition('.')[0]
        local_output = f"/tmp/k_{subdomain}-{epoch}_output.json"
        remote_output = f"metrics/k_{subdomain}-{epoch}_output.json"
        file_name = f"k_{subdomain}-{epoch}_output.json"
    else:
        local_output = f"/tmp/k_{attached_service.id}-{epoch}_output.json"
        remote_output = f"metrics/k_{attached_service.id}-{epoch}_output.json"
        file_name = f"k_{attached_service.id}-{epoch}_output.json"

    with open(local_output, 'w') as file:
        file.write(dumps(list(pedigrees)))

    multi_part_upload_with_s3(local_output, remote_output)

    data = {'data_path': remote_output,
            'file_name': file_name}

    coi_raw = requests.post(f'http://metrics.cloud-lines.com/api/metrics/{mother.id}/{father.id}/kinship/',
                            json=dumps(data, cls=DjangoJSONEncoder), stream=True)
    kin = KinshipQueue.objects.create(account=attached_service, user=request.user, mother=mother, father=father, file=file_name)
    response = {'status': 'message',
                'msg': "",
                'item_id': kin.id
                }
    return HttpResponse(dumps(response))


def kinship_results(request, id):
    attached_service = get_main_account(request.user)
    k_queue_item = KinshipQueue.objects.get(account=attached_service, id=id)
    resource = boto3.resource('s3')
    bucket = resource.Bucket(settings.AWS_S3_CUSTOM_DOMAIN)
    bucket.download_file(f"metrics/results-{k_queue_item.file}", f'/tmp/results-{k_queue_item.file}')

    with open(f'/tmp/results-{k_queue_item.file}') as results_file:
        kinship_raw = load(results_file)

    kinship_result = kinship_raw[str(k_queue_item.mother.id)][0][str(k_queue_item.father.id)]

    return render(request, 'k_results.html', {'k_queue_item': k_queue_item,
                                              'kinship_result': kinship_result})


def run_mean_kinship(request):
    attached_service = get_main_account(request.user)
    obj, created = MeanKinshipLastRun.objects.get_or_create(account=attached_service)

    obj.last_run = datetime.now()
    obj.save()
    # mk_thread = Thread(target=mean_kinship, args=(request, ))
    # mk_thread.start()
    mean_kinship(request)
    obj.last_run = calc_last_run(attached_service, obj)
    mean_kinship_date = obj.last_run.strftime("%b %d, %Y %H:%M:%S")
    return HttpResponse(dumps({'mean_kinship_date': mean_kinship_date}))


def mean_kinship(request):
    attached_service = get_main_account(request.user)
    breeds = Breed.objects.filter(account=attached_service)
    for breed in breeds.all():
        pedigrees = Pedigree.objects.filter(account=attached_service, breed=breed, status='alive').values('id',
                                                                                          'parent_father__id',
                                                                                          'parent_mother__id',
                                                                                          'sex',
                                                                                          'breed__breed_name',
                                                                                          'status')
        if len(pedigrees) > 1:
            # create unique paths
            if attached_service.service.service_name in ('Small Society', 'Large Society', 'Organisation'):
                host = attached_service.domain.partition('://')[2]
                subdomain = host.partition('.')[0]
                local_output = f"/tmp/mk_{subdomain}_output.json"
                remote_output = f"metrics/mk_{subdomain}_output.json"
                file_name = f"mk_{subdomain}_output.json"
            else:
                local_output = f"/tmp/mk_{attached_service.id}_output.json"
                remote_output = f"metrics/mk_{attached_service.id}_output.json"
                file_name = f"mk_{attached_service.id}_output.json"

            with open(local_output, 'w') as file:
                file.write(dumps(list(pedigrees)))

            multi_part_upload_with_s3(local_output, remote_output)

            data = {'data_path': remote_output,
                    'file_name': file_name,
                    'domain': attached_service.domain}

            coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/mean_kinship/',
                                    json=dumps(data, cls=DjangoJSONEncoder), stream=True)

            # coi_dict = loads(coi_raw.json())
            # for pedigree, value in coi_dict.items():
            #     Pedigree.objects.filter(account=attached_service, id=pedigree.strip('X')).update(mean_kinship=value['1'])


def stud_advisor_mother_details(request, mother):
    attached_service = get_main_account(request.user)
    cois = Pedigree.objects.filter(account=attached_service, breed=mother.breed, status='alive').values('coi')
    total = 0
    for coi in cois.all():
        total += coi['coi']
    breed_mean_coi = total / Pedigree.objects.filter(account=attached_service, breed=mother.breed, status__icontains='alive').count()

    mother_details = {'reg_no': mother.reg_no,
                      'name': mother.name,
                      'mk': str(mother.mean_kinship),
                      'breed': mother.breed.breed_name,
                      'threshold': str(mother.breed.mk_threshold),
                      'breed_mean_coi': str(breed_mean_coi)}
    return HttpResponse(dumps(mother_details))


def stud_advisor(request):
    attached_service = get_main_account(request.user)
    epoch = int(time())

    mother = request.POST['mother']
    mother = Pedigree.objects.get(account=attached_service, reg_no=mother)

    pedigrees = Pedigree.objects.filter(account=attached_service,
                                        breed=mother.breed).values('id',
                                                                   'parent_father__id',
                                                                   'parent_mother__id',
                                                                   'sex',
                                                                   'breed__breed_name',
                                                                   'status')

    if attached_service.service.service_name in ('Small Society', 'Large Society', 'Organisation'):
        host = attached_service.domain.partition('://')[2]
        subdomain = host.partition('.')[0]
        local_output = f"/tmp/sa_{subdomain}-{epoch}_output.json"
        remote_output = f"metrics/sa_{subdomain}-{epoch}_output.json"
        file_name = f"sa_{subdomain}-{epoch}_output.json"
    else:
        local_output = f"/tmp/sa_{attached_service.id}-{epoch}_output.json"
        remote_output = f"metrics/sa_{attached_service.id}-{epoch}_output.json"
        file_name = f"sa_{attached_service.id}-{epoch}_output.json"

    with open(local_output, 'w') as file:
        file.write(dumps(list(pedigrees)))

    multi_part_upload_with_s3(local_output, remote_output)

    data = {'data_path': remote_output,
            'file_name': file_name}

    coi_raw = requests.post('http://metrics.cloud-lines.com/api/metrics/stud_advisor/',
                            json=dumps(data, cls=DjangoJSONEncoder), stream=True)
    sa = StudAdvisorQueue.objects.create(account=attached_service, user=request.user, mother=mother, file=file_name)
    response = {'status': 'message',
                'msg': "",
                'item_id': sa.id
                }
    return HttpResponse(dumps(response))


def stud_advisor_results(request, id):
    attached_service = get_main_account(request.user)
    sa_queue_item = StudAdvisorQueue.objects.get(account=attached_service, id=id)
    mother_details = stud_advisor_mother_details(request, sa_queue_item.mother)
    mother_details = eval(mother_details.content.decode())


    with urllib.request.urlopen(f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/metrics/results-{sa_queue_item.file}") as results_file:
        studs_raw = loads(results_file.read().decode())

    studs_data = calculate_sa_thresholds(studs_raw, attached_service, sa_queue_item.mother, mother_details)

    return render(request, 'sa_results.html', {'stud_data': studs_data,
                                               'sa_queue_item': sa_queue_item,
                                               'mother_details': mother_details})


def results_complete(request):
    # get queue item
    stud_item = StudAdvisorQueue.objects.filter(id=request.POST.get('item_id'), complete=False)
    kin_item = KinshipQueue.objects.filter(id=request.POST.get('item_id'), complete=False)
    queue_items = sorted(chain(stud_item, kin_item))
    if len(queue_items) > 0:
        # process only the first item in the queue list
        item = queue_items[0]
        # check if item is complete
        tld = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/"
        results_file = requests.get(urllib.parse.urljoin(tld, f"metrics/results-{item.file}"))
        # set item to complete if it's true
        if results_file.status_code == 200:
            item.complete = True
            item.save()

        return HttpResponse(dumps({'result': 'success', 'complete': item.complete}))
    # queue item not found
    else:
        return HttpResponse(dumps({'result': 'fail'}))


def calculate_sa_thresholds(studs_raw, attached_service, mother, mother_details):
    studs_data = {}
    for stud, kinship in studs_raw[str(mother.id)][0].items():
        try:
            male = Pedigree.objects.get(account=attached_service, id=stud, sex='male', status='alive')
            mk_minus_mk_thresh = mother.mean_kinship - mother.breed.mk_threshold
            mk_plus_mk_thresh = mother.mean_kinship + mother.breed.mk_threshold
            mk_minus_mk_thresh_2 = mother.mean_kinship - (mother.breed.mk_threshold*2)
            mk_plus_mk_thresh_2 = mother.mean_kinship + (mother.breed.mk_threshold*2)

            if mk_minus_mk_thresh <= male.mean_kinship <= mk_plus_mk_thresh\
                    and kinship <= float(mother_details['breed_mean_coi']):
                color = 'green'
            elif mk_minus_mk_thresh_2 <= male.mean_kinship <= mk_plus_mk_thresh_2\
                    and kinship <= float(mother_details['breed_mean_coi']):
                color = 'orange'
            elif mk_minus_mk_thresh_2 <= male.mean_kinship <= mk_plus_mk_thresh_2\
                    and kinship > float(mother_details['breed_mean_coi']):
                color = 'red'
            else:
                color = None

            if color:
                studs_data[stud] = {'id': male.id,
                                    'reg_no': male.reg_no,
                                    'name': male.name,
                                    'mean_kinship': str(male.mean_kinship),
                                    'kinship': kinship,
                                    'color': color}
        except ObjectDoesNotExist:
            continue

    return studs_data


def poprep_export(request):
    from datetime import datetime
    import csv

    date = datetime.now()
    attached_service = get_main_account(request.user)
    breed = Breed.objects.get(id=request.POST['breed'])

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="PopRep-Export-{}-{}.csv"'.format(breed,
        date.strftime("%Y-%m-%d"))

    writer = csv.writer(response, delimiter="|")

    for pedigree in Pedigree.objects.filter(account=attached_service, breed=breed).exclude(state='unapproved').values('reg_no', 'parent_father__reg_no', 'parent_mother__reg_no', 'dob', 'sex'):
        if pedigree['sex'] == "male":
            sex = "M"
        elif pedigree['sex'] == "female":
            sex = "F"
        elif pedigree['sex'] == "castrated":
            sex = "M"
        else:
            sex = ""

        writer.writerow([pedigree['reg_no'], pedigree['parent_father__reg_no'], pedigree['parent_mother__reg_no'], pedigree['dob'], sex])

    return response