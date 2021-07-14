#!/usr/bin/python3
import django
import sys
import os
from datetime import datetime
import boto3
from botocore.config import Config


sys.path.append('/opt/cloudlines/cloud-lines')
os.environ["DJANGO_SETTINGS_MODULE"] = "cloudlines.settings"
django.setup()

# from cloud_lines.models import LargeTierQueue
# from account.views import send_mail
from pedigree.models import Pedigree
from impex.models import ExportQueue


class Export:
    def __init__(self):
        self.waiting = ExportQueue.objects.filter(status="waiting")

    def run(self, export):
        date = datetime.now()
        filename = f'cloud-lines-pedigrees-{date.strftime("%Y-%m-%d")}.csv'

        header = False

        for pedigree in Pedigree.objects.filter(account=export.attached_service):
            head = []
            row = []
            for key, val in pedigree.__dict__.items():
                if key not in ('_state', 'state', 'id', 'creator_id', 'account_id', 'breed_group', 'date_added'):
                    # load custom fields
                    if key == 'custom_fields':
                        try:
                            custom_fields = dict(loads(pedigree.custom_fields)).values()
                        except JSONDecodeError:
                            custom_fields = {}

                    if not header:
                        if key == 'custom_fields':
                            # add a columns for each custom field
                            for field in custom_fields:
                                head.append(field['fieldName'])
                        else:
                            # use verbose names of the pedigree fields as field names
                            head.append(Pedigree._meta.get_field(key).verbose_name)

                    if key == 'parent_mother_id' or key == 'parent_father_id':
                        try:
                            parent = Pedigree.objects.get(id=val)
                            reg_no = parent.reg_no.strip()
                        except ObjectDoesNotExist:
                            reg_no = ""
                        row.append('{}'.format(reg_no))
                    elif key == 'breeder_id':
                        try:
                            breeder = Breeder.objects.get(id=val)
                            breed_prefix = breeder.breeding_prefix
                        except ObjectDoesNotExist:
                            breed_prefix = ""
                        row.append('{}'.format(breed_prefix))
                    elif key == 'current_owner_id':
                        try:
                            current_owner = Breeder.objects.get(id=val)
                            current_owner_prefix = current_owner.breeding_prefix
                        except ObjectDoesNotExist:
                            current_owner_prefix = ""
                        row.append('{}'.format(current_owner_prefix))
                    elif key == 'breed_id':
                        try:
                            breed = Breed.objects.get(id=val)
                            breed_name = breed.breed_name
                        except ObjectDoesNotExist:
                            breed_name = ""
                        row.append('{}'.format(breed_name))
                    elif key == 'custom_fields':
                        # populate each custom field column with the value
                        for field in custom_fields:
                            if 'field_value' in field:
                                row.append(field['field_value'])
                            else:
                                row.append('')
                    elif key == 'sale_or_hire':
                        if pedigree.sale_or_hire:
                            row.append('yes')
                        else:
                            row.append('no')
                    # make sure 'None' isn't given for dates, and that they're formatted well
                    elif key == 'date_of_registration':
                        if pedigree.date_of_registration:
                            row.append(pedigree.date_of_registration.strftime('%d/%m/%Y'))
                        else:
                            row.append('')
                    elif key == 'dob':
                        if pedigree.dob:
                            row.append(pedigree.dob.strftime('%d/%m/%Y'))
                        else:
                            row.append('')
                    elif key == 'dod':
                        if pedigree.dod:
                            row.append(pedigree.dod.strftime('%d/%m/%Y'))
                        else:
                            row.append('')
                    else:
                        row.append('{}'.format(val))
            if not header:
                writer.writerow(head)
                header = True
            writer.writerow(row)

        return response


if __name__ == '__main__':
    lt = Export()
    for item in lt.waiting:
        lt.run(item)
