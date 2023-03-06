import re

from .models import Pedigree


def get_pedigree_column_headings():
    # get pedigree model headings
    forbidden_pedigree_fields = ['id', 'creator', 'account', 'date_added', 'state', 'breed_group', 'custom_fields']
    return [field for field in Pedigree._meta.get_fields(include_parents=False, include_hidden=False) if
                         field.name not in forbidden_pedigree_fields]


def get_site_pedigree_column_headings(atatched_service):
    pedigree_mapping = {'breeder': {'db_id': 'breeder__breeding_prefix',
                                    'db_id_internal': 'breeder.breeding_prefix',
                                    'name': 'Breeder',
                                    'upper': False,
                                    'html': ''},
                        'current_owner': {'db_id': 'current_owner__breeding_prefix',
                                          'db_id_internal': 'current_owner.breeding_prefix',
                                          'name': 'Current Owner',
                                          'upper': False,
                                          'html': ''},
                        'reg_no': {'db_id': 'reg_no',
                                   'db_id_internal': 'reg_no',
                                   'name': 'Reg No',
                                   'upper': True,
                                   'html': ''},
                        'tag_no': {'db_id': 'tag_no',
                                   'db_id_internal': 'tag_no',
                                   'name': 'Tag No.',
                                   'upper': False,
                                   'html': ''},
                        'name': {'db_id': 'name',
                                 'db_id_internal': 'name',
                                 'name': 'Name',
                                 'upper': False,
                                 'html': ''},
                        'description': {'db_id': 'description',
                                        'db_id_internal': 'description',
                                        'name': 'Description',
                                        'upper': False,
                                        'html': ''},
                        'date_of_registration': {'db_id': 'date_of_registration',
                                                 'db_id_internal': 'date_of_registration.strftime(format="%d-%m-%Y")',
                                                 'name': 'Date of Registration',
                                                 'upper': False,
                                                 'html': ''},
                        'dob': {'db_id': 'dob',
                                'db_id_internal': 'dob.strftime(format="%d-%m-%Y")',
                                'name': 'Date of Birth',
                                'upper': False,
                                'html': ''},
                        'dod': {'db_id': 'dod',
                                'db_id_internal': 'dod.strftime(format="%d-%m-%Y")',
                                'name': 'Date of Death',
                                'upper': False,
                                'html': ''},
                        'status': {'db_id': 'status',
                                   'db_id_internal': 'status',
                                   'name': 'Status',
                                   'upper': False,
                                   'html': ''},
                        'sex': {'db_id': 'sex',
                                'db_id_internal': 'sex',
                                'name': 'Sex',
                                'upper': False,
                                'html': """<span class="label label-primary"> %REPLACEME% </span>"""},
                        'litter_size': {'db_id': 'litter_size',
                                    'db_id_internal': 'litter_size',
                                    'name': 'Litter Size',
                                    'upper': False,
                                    'html': ''},
                        'parent_father': {'db_id': 'parent_father__reg_no',
                                          'db_id_internal': 'parent_father.reg_no',
                                          'name': atatched_service.father_title,
                                          'upper': True,
                                          'html': ''},
                        'parent_father_notes': {'db_id': 'parent_father_notes',
                                                'db_id_internal': 'parent_father_notes',
                                                'name': f'{atatched_service.father_title} Notes',
                                                'upper': False,
                                                'html': ''},
                        'parent_mother': {'db_id': 'parent_mother__reg_no',
                                          'db_id_internal': 'parent_mother.reg_no',
                                          'name': atatched_service.mother_title,
                                          'upper': True,
                                          'html': ''},
                        'parent_mother_notes': {'db_id': 'parent_mother_notes',
                                                'db_id_internal': 'parent_mother_notes',
                                                'name': f'{atatched_service.mother_title} Notes',
                                                'upper': False,
                                                'html': ''},
                        'breed_group': {'db_id': 'breed_group__group_name',
                                        'db_id_internal': 'breed_group.group_name',
                                        'name': 'Breed Group',
                                        'upper': False,
                                        'html': ''},
                        'breed': {'db_id': 'breed__breed_name',
                                  'db_id_internal': 'breed.breed_name',
                                  'name': 'Breed',
                                  'upper': False,
                                  'html': ''},
                        'coi': {'db_id': 'coi',
                                'db_id_internal': 'coi.to_eng_string()',
                                'name': 'COI',
                                'upper': False,
                                'html': ''},
                        'mean_kinship': {'db_id': 'mean_kinship',
                                         'db_id_internal': 'mean_kinship.to_eng_string()',
                                         'name': 'Mean Kinship',
                                         'upper': False,
                                         'html': ''},
                        'sale_or_hire': {'db_id': 'sale_or_hire',
                                         'db_id_internal': 'sale_or_hire',
                                         'name': 'For Sale/Hire',
                                         'upper': False,
                                         'html': ''},
                        }

    site_columns = atatched_service.pedigree_columns.split(',')
    columns = []
    for column in site_columns:
        columns.append(pedigree_mapping[column]['db_id'])
    return columns, pedigree_mapping


def get_next_reg(attached_service):
    # get next available reg number
    try:
        latest_added = Pedigree.objects.filter(account=attached_service).latest('id')
        latest_reg = latest_added.reg_no
        reg_ints_re = re.search("[0-9]+", latest_reg)
        suggested_reg = latest_reg.replace(str(reg_ints_re.group(0)), str(int(reg_ints_re.group(0))+1).zfill(len(reg_ints_re.group(0))))
    except Pedigree.DoesNotExist:
        suggested_reg = 'REG123456'
    except AttributeError:
        suggested_reg = 'REG123456'

    # if reg taken, increment until not taken
    if suggested_reg == 'REG123456':
        while Pedigree.objects.filter(account=attached_service, reg_no=suggested_reg).exists():
            reg_ints_re = re.search("[0-9]+", suggested_reg)
            suggested_reg = suggested_reg.replace(str(reg_ints_re.group(0)), str(int(reg_ints_re.group(0))+1).zfill(len(reg_ints_re.group(0))))
    return suggested_reg