from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from pedigree.models import Pedigree
from account.views import is_editor, get_main_account
from datetime import datetime
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


def importx(request):
    return render(request, 'import.html')