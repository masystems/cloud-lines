from django.shortcuts import render, HttpResponse
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.conf import settings
from rest_framework.authtoken.models import Token
from account.views import is_editor, get_main_account, send_mail
from pedigree.models import Pedigree
from breed.models import Breed
from django.core.serializers.json import DjangoJSONEncoder
from .models import CoiLastRun, MeanKinshipLastRun, StudAdvisorQueue, KinshipQueue, DataValidatorQueue
from json import dumps, loads
from datetime import datetime, timedelta
import logging
import requests
import pytz
import boto3
import urllib.parse
import urllib.request
from time import time
from boto3.s3.transfer import TransferConfig
from itertools import chain

from account.views import has_permission, redirect_2_login
from django.contrib.auth.decorators import login_required


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
    dv_queue = DataValidatorQueue.objects.filter(account=attached_service).last()
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
                                            'queue_items': queue_items,
                                            'dv_queue': dv_queue})


def multi_part_upload_with_s3(file_path, key_path):
    s3 = boto3.resource('s3')
    # Multipart upload
    config = TransferConfig(multipart_threshold=1024 * 10, max_concurrency=10,
                            multipart_chunksize=1024 * 10, use_threads=True)
    s3.meta.client.upload_file(file_path, settings.AWS_S3_CUSTOM_DOMAIN, key_path,
                            ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/json'},
                            Config=config,
                            )


def data_validation(request):
    attached_service = get_main_account(request.user)
    dv = DataValidatorQueue.objects.create(account=attached_service,
                                           user=request.user,
                                           )

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
        local_output = f"/tmp/dv_{subdomain}_output.json"
        remote_output = f"metrics/dv_{subdomain}_output.json"
        file_name = f"dv_{subdomain}_output.json"
    else:
        local_output = f"/tmp/dv_{attached_service.id}_output.json"
        remote_output = f"metrics/dv_{attached_service.id}_output.json"
        file_name = f"dv_{attached_service.id}_output.json"

    with open(local_output, 'w') as file:
        file.write(dumps(list(pedigrees)))

    multi_part_upload_with_s3(local_output, remote_output)

    token, created = Token.objects.get_or_create(user=request.user)

    data = {'data_path': remote_output,
            'file_name': file_name,
            'domain': attached_service.domain,
            'dv_q_id': dv.id,
            'token': str(token)}

    coi_raw = requests.post(urllib.parse.urljoin(settings.METRICS_URL, "/api/metrics/data_validator/"),
                            json=dumps(data, cls=DjangoJSONEncoder))

    response = {'status': 'success'}
    return HttpResponse(dumps(response))


def run_coi(request):
    # check permission (this is only used to receive POST requests)
    if request.method == 'GET':
        return redirect_2_login(request)
    elif request.method == 'POST':
        pedigree = Pedigree.objects.filter(breed__id=request.POST.get('breed')).first()
        if not pedigree:
            raise PermissionDenied()
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': 'breed'}, pedigrees=[pedigree]):
            raise PermissionDenied()
    else:
        raise PermissionDenied()

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
    pedigrees = Pedigree.objects.filter(account=attached_service, breed__id=request.POST['breed']).values('id',
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

    token, created = Token.objects.get_or_create(user=request.user)

    data = {'data_path': remote_output,
            'file_name': file_name,
            'domain': attached_service.domain,
            'token': str(token)}

    coi_raw = requests.post(urllib.parse.urljoin(settings.METRICS_URL, "/api/metrics/coi/"),
                            json=dumps(data, cls=DjangoJSONEncoder))

    #coi_dict = loads(coi_raw.json())


def kinship(request):
    # check permission (this is only used to receive POST requests)
    # the specific breed is checked later
    if request.method == 'GET':
        return redirect_2_login(request)
    elif request.method == 'POST':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': True}):
            response = {'status': 'error',
                        'msg': "You do not have permission!"
                        }
            return HttpResponse(dumps(response))
    else:
        raise PermissionDenied()
    
    attached_service = get_main_account(request.user)
    epoch = int(time())
    pedigrees = Pedigree.objects.filter(account=attached_service).values('id',
                                                                         'parent_father__id',
                                                                         'parent_mother__id',
                                                                         'sex',
                                                                         'breed__breed_name',
                                                                         'status')

    # check mother exists
    try:
        mother = Pedigree.objects.get(reg_no=request.POST['mother'])
    except Pedigree.DoesNotExist:
        response = {'status': 'error',
                    'msg': f"Mother ({request.POST['mother']}) does not exist!"
                    }
        return HttpResponse(dumps(response))
    
    # check mother is a living female
    if mother.sex.lower() != 'female' or mother.status.lower() != 'alive':
        response = {'status': 'error',
                    'msg': f"Mother ({request.POST['mother']}) is not a living female!"
                    }
        return HttpResponse(dumps(response))
    
    # check father exists
    try:
        father = Pedigree.objects.get(reg_no=request.POST['father'])
    except Pedigree.DoesNotExist:
        response = {'status': 'error',
                    'msg': f"Father ({request.POST['father']}) does not exist!"
                    }
        return HttpResponse(dumps(response))

    # check that father is a living male
    if father.sex.lower() != 'male' or father.status.lower() != 'alive':
        response = {'status': 'error',
                    'msg': f"Father ({request.POST['father']}) is not a living male!"
                    }
        return HttpResponse(dumps(response))
    
    breeds_editable = request.POST.get('breeds-editable').replace('[', '').replace(']', '').replace("&#39;", '').replace("'", '').replace(', ', ',').split(',')
    if '' in breeds_editable:
        breeds_editable.remove('')
    # if user is a breed admin
    if len(breeds_editable) > 0:
        # check that the breed of the mother is editable
        if request.user not in mother.breed.breed_admins.all():
            response = {'status': 'error',
                        'msg': f"The breed of mother ({request.POST['mother']}) is not a breed you are an editor for!"
                        }
            return HttpResponse(dumps(response))

        # check that the breed of the father is editable
        if request.user not in father.breed.breed_admins.all():
            response = {'status': 'error',
                        'msg': f"The breed of father ({request.POST['father']}) is not a breed you are an editor for!"
                        }
            return HttpResponse(dumps(response))

    # check that the mother and father are of the same breed
    if mother.breed != father.breed:
        response = {'status': 'error',
                        'msg': f"The breed of mother ({request.POST['mother']}) does not match the breed of father ({request.POST['father']})!"
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

    kin = KinshipQueue.objects.create(account=attached_service, user=request.user, mother=mother, father=father,
                                      file=file_name)
    kin.save()
    token, created = Token.objects.get_or_create(user=request.user)
    data = {'data_path': remote_output,
            'file_name': file_name,
            'domain': attached_service.domain,
            'kin_q_id': kin.id,
            'token': str(token)}

    coi_raw = requests.post(urllib.parse.urljoin(settings.METRICS_URL, f'/api/metrics/{mother.id}/{father.id}/kinship/'),
                            json=dumps(data, cls=DjangoJSONEncoder), stream=True)

    if coi_raw.status_code == 200:
        response = {'status': 'message',
                    'msg': "",
                    'item_id': kin.id
                    }
    else:
        kin.delete()
        send_mail('Metrics server down', "Metrics", "Check Metrics server")
        response = {'status': 'fail',
                    'msg': "Failed to communicate with the server!",
                    'item_id': ''
                    }
    return HttpResponse(dumps(response))


@login_required(login_url="/account/login")
def kinship_results(request, id):
    attached_service = get_main_account(request.user)
    k_queue_item = KinshipQueue.objects.get(account=attached_service, id=id)

    # check if user has permission, passing in ids of mother and father from kinship queue item
    # this is only used for GET requests
    if request.method == 'GET':
        if not has_permission(request, {'read_only': False, 'contrib': True, 'admin': True, 'breed_admin': 'breed'},
                                    pedigrees=[k_queue_item.mother ,k_queue_item.father]):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()

    return render(request, 'k_results.html', {'k_queue_item': k_queue_item})


def run_mean_kinship(request):
    # check permission (this is only used to receive POST requests)
    if request.method == 'GET':
        return redirect_2_login(request)
    elif request.method == 'POST':
        pedigree = Pedigree.objects.filter(breed__id=request.POST.get('breed')).first()
        if not pedigree:
            raise PermissionDenied()
        if not has_permission(request, {'read_only': False, 'contrib': False, 'admin': True, 'breed_admin': 'breed'}, pedigrees=[pedigree]):
            raise PermissionDenied()
    else:
        raise PermissionDenied()
    
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
    
    pedigrees = Pedigree.objects.filter(account=attached_service, breed=request.POST['breed'], status='alive').values('id',
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

        token, created = Token.objects.get_or_create(user=request.user)

        data = {'data_path': remote_output,
                'file_name': file_name,
                'domain': attached_service.domain,
                'token': str(token)}

        coi_raw = requests.post(urllib.parse.urljoin(settings.METRICS_URL, '/api/metrics/mean_kinship/'),
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
    return mother_details


def stud_advisor(request):
    attached_service = get_main_account(request.user)
    epoch = int(time())

    mother = request.POST['mother']
    
    try:
        mother = Pedigree.objects.get(account=attached_service, reg_no=mother)
    except Pedigree.DoesNotExist:
        response = {
            'status': 'fail',
            'msg': f"Mother ({request.POST['mother']}) does not exist",
            'item_id': ''
        }
        return HttpResponse(dumps(response))
    
    # check permission (this is only used to receive POST requests)
    # the specific breed is checked later
    if request.method == 'GET':
        return redirect_2_login(request)
    elif request.method == 'POST':
        # get breeder users
        breeder_users = []
        if mother.current_owner:
            if mother.current_owner.user:
                breeder_users.append(mother.current_owner.user)
        if not has_permission(request, {'read_only': 'breeder', 'contrib': 'breeder', 'admin': True, 'breed_admin': True}, 
                                        breeder_users=breeder_users):
            response = {'status': 'fail',
                        'msg': "You do not have permission!",
                        'item_id': ''
                        }
            return HttpResponse(dumps(response))
    else:
        raise PermissionDenied()

    # check that mother is a living female
    if mother.sex.lower() != 'female' or mother.status.lower() != 'alive':
        response = {
            'status': 'fail',
            'msg': f"Mother ({request.POST['mother']}) is not a living female!",
            'item_id': ''
        }
        return HttpResponse(dumps(response))

    breeds_editable = request.POST.get('breeds-editable').replace('[', '').replace(']', '').replace("&#39;", '').replace("'", '').replace(', ', ',').split(',')
    if '' in breeds_editable:
        breeds_editable.remove('')
    # if user is a breed admin
    if len(breeds_editable) > 0:
        # check that the breed of the mother is editable
        if request.user not in mother.breed.breed_admins.all():
            response = {
                'status': 'fail',
                'msg': f"The breed of mother ({request.POST['mother']}) is not a breed you are an editor for!",
                'item_id': ''
            }
            return HttpResponse(dumps(response))

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

    token, created = Token.objects.get_or_create(user=request.user)

    mother_details = stud_advisor_mother_details(request, mother)

    sa = StudAdvisorQueue.objects.create(account=attached_service, user=request.user, mother=mother, file=file_name,
                                         mk_threshold=mother.breed.mk_threshold)

    data = {'data_path': remote_output,
            'file_name': file_name,
            'domain': attached_service.domain,
            'mother_id': mother.id,
            'mother_mk': mother.mean_kinship,
            'mother_breed_mean_coi': mother_details['breed_mean_coi'],
            'mother_breed_mk_threshold': mother.breed.mk_threshold,
            'token': str(token),
            'queue_id': sa.id}

    coi_raw = requests.post(urllib.parse.urljoin(settings.METRICS_URL, '/api/metrics/stud_advisor/'),
                            json=dumps(data, cls=DjangoJSONEncoder), stream=True)
    if coi_raw.status_code == 200:
        response = {'status': 'message',
                    'msg': "",
                    'item_id': sa.id
                    }
        return HttpResponse(dumps(response))
    else:
        sa.delete()
        send_mail('Metrics server down', "Metrics", "Check Metrics server")
        response = {'status': 'fail',
                    'msg': "Failed to communicate with the server!",
                    'item_id': ''
                    }
        return HttpResponse(dumps(response))


def stud_advisor_results(request, id):
    attached_service = get_main_account(request.user)
    sa_queue_item = StudAdvisorQueue.objects.get(account=attached_service, id=id)

    # check permission
    if request.method == 'GET':
        # get breeder users
        breeder_users = []
        if sa_queue_item.mother.current_owner:
            if sa_queue_item.mother.current_owner.user:
                breeder_users.append(sa_queue_item.mother.current_owner.user)
        if not has_permission(request, {'read_only': 'breeder', 'contrib': 'breeder', 'admin': True, 'breed_admin': 'breed'},
                                    pedigrees=[sa_queue_item.mother],
                                    breeder_users=breeder_users):
            return redirect_2_login(request)
    else:
        raise PermissionDenied()

    mother_details = stud_advisor_mother_details(request, sa_queue_item.mother)
    #mother_details = eval(mother_details.content.decode())
    mk_threshold = sa_queue_item.mk_threshold

    with urllib.request.urlopen(f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/metrics/results-{sa_queue_item.file}") as results_file:
        results_raw = loads(results_file.read().decode())

    #studs_data = calculate_sa_thresholds(studs_raw, attached_service, sa_queue_item.mother, mother_details)

    return render(request, 'sa_results.html', {'results_raw': results_raw,
                                               'sa_queue_item': sa_queue_item,
                                               'mother_details': mother_details,
                                               'mk_threshold': mk_threshold})


def results_complete(request):
    # get queue item
    stud_items = StudAdvisorQueue.objects.filter(id=request.POST.get('item_id'),
                                                 complete=False,
                                                 failed=False)
    kin_items = KinshipQueue.objects.filter(id=request.POST.get('item_id'),
                                            result__isnull=False,
                                            complete=True,
                                            failed=False)
    hrs24 = datetime.now() - timedelta(days=1)
    for stud in stud_items:
        if stud.created < hrs24:
            stud.failed = True
            stud.complete = True
            stud.save()
            return HttpResponse(dumps({'result': 'fail', 'status': 'expired'}))
    for kin in kin_items:
        if kin.created < hrs24:
            kin.failed = True
            kin.complete = True
            kin.save()
            return HttpResponse(dumps({'result': 'fail', 'status': 'expired'}))

    if stud_items.count() > 0:
        res = get_results_from_s3(stud_items)
        return res
    if kin_items.count() > 0:
        item = kin_items[0]
        return HttpResponse(dumps({'result': 'success', 'complete': item.complete}))
    return HttpResponse(dumps({'result': 'fail'}))


def get_results_from_s3(queue_items):

    # process only the first item in the queue list
    item = queue_items[0]
    # check if item is complete
    tld = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/"
    results_file = requests.get(urllib.parse.urljoin(tld, f"metrics/results-{item.file}"))

    if results_file.status_code == 200:
        item.complete = True
        item.save()
    else:
        # queue item not found
        return HttpResponse(dumps({'result': 'fail'}))

    return HttpResponse(dumps({'result': 'success', 'complete': item.complete}))


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

    for pedigree in Pedigree.objects.filter(account=attached_service, breed=breed).exclude(Q(state='unapproved') | Q(status='unknown') | Q(sex='unknown')).values('reg_no', 'parent_father__reg_no', 'parent_mother__reg_no', 'dob', 'sex'):
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