from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from pedigree.models import Pedigree
from breeder.models import Breeder
from account.views import is_editor, get_main_account
from .models import DatabaseUpload
from datetime import datetime
from os.path import splitext
import csv


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def export(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        fields = request.POST.getlist('fields')
        date = datetime.now()
        if request.POST['submit'] == 'xlsx':
            pass
        elif request.POST['submit'] == 'csv':
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="pedigree_db{}.csv"'.format(date.strftime("%Y-%m-%d"))

            writer = csv.writer(response)
            header = False

            for pedigree in Pedigree.objects.filter(account=attached_service):
                head = ''
                row = ''
                for key, val in pedigree.__dict__.items():
                    if not header:
                        if key != '_state':
                            head += '{},'.format(key)
                    if key in fields:
                        row += '{},'.format(val)
                if not header:
                    writer.writerow([head])
                    header = True
                writer.writerow([row])

            return response
        elif request.POST['submit'] == 'pdf':
            pass

    return render(request, 'export.html', {'fields': Pedigree._meta.get_fields(include_parents=False, include_hidden=False)})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def importx(request):
    allowed_file_types = ('.xls', 'xlsx', '.csv')
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        database_file = request.FILES['uploadDatabase']
        imported_headings = []

        f_type = splitext(str(request.FILES['uploadDatabase']))[1]
        if f_type not in allowed_file_types:
            return render(request, 'import.html', {'error': '{} is not an allowed file type!'.format(f_type)})

        if f_type == '.csv':
            file = request.FILES['uploadDatabase']
            decoded_file = file.read().decode('utf-8').splitlines()
            database_items = csv.DictReader(decoded_file)
            imported_headings = database_items.fieldnames

        # upload file
        upload_database = DatabaseUpload(account=attached_service, database=database_file, file_type=f_type)
        upload_database.save(database_file)

        # get model headings
        forbidden_fields = ['id', 'creator', 'account', 'date_added']
        pedigree_headings = [field for field in Pedigree._meta.get_fields(include_parents=False, include_hidden=False) if field.name not in forbidden_fields]

        return render(request, 'analyse.html', {'imported_headings': imported_headings,
                                                'pedigree_headings': pedigree_headings})
    return render(request, 'import.html')


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def import_data(request):
    if request.method == 'POST':
        attached_service = get_main_account(request.user)
        db = DatabaseUpload.objects.filter(account=attached_service).latest('id')
        decoded_file = db.database.file.read().decode('utf-8').splitlines()
        database_items = csv.DictReader(decoded_file)
        date_fields = ['date_of_registration', 'dob', 'dod']
        post_data = {}

        # remove blank ('---') entries
        for key, val in request.POST.items():
            if val == '---':
                if key in date_fields:
                    post_data[key] = None
                post_data[key] = ''
            else:
                post_data[key] = val

        # get all options
        breeder = post_data['breeder']
        current_owner = post_data['current_owner']
        reg_no = post_data['reg_no'] or ''
        tag_no = post_data['tag_no'] or ''
        name = post_data['name'] or None
        description = post_data['description'] or ''
        date_of_registration = post_data['date_of_registration'] or ''
        dob = post_data['dob'] or ''
        dod = post_data['dod'] or ''
        sex = post_data['sex'] or ''
        note = post_data['note'] or ''

        for row in database_items:
            # create breeder if it doesn't exist
            if not breeder:
                breeder, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[breeder])

            # create current owner if it doesn't exist
            if not current_owner:
                current_owner, created = Breeder.objects.get_or_create(account=attached_service, breeding_prefix=row[current_owner])

            # create each new pedigree
            pedigree, created = Pedigree.objects.get_or_create(account=attached_service, reg_no=row[reg_no])
            pedigree.creator = request.user
            try:
                pedigree.breeder = breeder
            except ValueError:
                pass
            try:
                pedigree.current_owner = current_owner
            except ValueError:
                pass
            pedigree.tag_no = row[tag_no]
            pedigree.name = row[name]
            pedigree.description = row[description]
            try:
                pedigree.date_of_registration = row[date_of_registration]
            except ValidationError:
                pass
            try:
                pedigree.dob = row[dob]
            except ValidationError:
                pass
            try:
                pedigree.dod = row[dod]
            except ValidationError:
                pass
            pedigree.sex = row[sex]
            pedigree.note = row[note]

            print(pedigree)
            pedigree.save()

