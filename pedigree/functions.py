from .models import Pedigree


def get_pedigree_column_headings():
    # get pedigree model headings
    forbidden_pedigree_fields = ['id', 'creator', 'account', 'date_added', 'state', 'custom_fields']
    return [field for field in Pedigree._meta.get_fields(include_parents=False, include_hidden=False) if
                         field.name not in forbidden_pedigree_fields]


def get_site_pedigree_column_headings(atatched_service):
    pedigree_mapping = {'breeder': {'db_id': 'breeder__breeder_prefix',
                                    'name': 'Breeder',
                                    'upper': False,
                                    'html': ''},
                        'current_owner': {'db_id': 'current_owner__breeder_prefix',
                                          'name': 'Current Owner',
                                          'upper': False,
                                          'html': ''},
                        'reg_no': {'db_id': 'reg_no',
                                   'name': 'Reg No.',
                                   'upper': True,
                                   'html': ''},
                        'tag_no': {'db_id': 'tag_no',
                                   'name': 'Tag No.',
                                   'upper': False,
                                   'html': ''},
                        'name': {'db_id': 'name',
                                 'name': 'Name',
                                 'upper': False,
                                 'html': ''},
                        'description': {'db_id': 'description',
                                        'name': 'Name',
                                        'upper': False,
                                        'html': ''},
                        'date_of_registration': {'db_id': 'date_of_registration',
                                                 'name': 'Date of Registration',
                                                 'upper': False,
                                                 'html': ''},
                        'dob': {'db_id': 'dob',
                                'name': 'Date of Birth',
                                'upper': False,
                                'html': ''},
                        'dod': {'db_id': 'dod',
                                'name': 'Date of Birth',
                                'upper': False,
                                'html': ''},
                        'status': {'db_id': 'status',
                                   'name': 'Status',
                                   'upper': False,
                                   'html': ''},
                        'sex': {'db_id': 'sex',
                                'name': 'Sex',
                                'upper': False,
                                'html': """<span class="label label-primary"> %REPLACEME% </span>"""},
                        'parent_father': {'db_id': 'parent_father__reg_no',
                                          'name': atatched_service.father_title,
                                          'upper': True,
                                          'html': ''},
                        'parent_father_notes': {'db_id': 'parent_father_notes',
                                                'name': f'{atatched_service.father_title} Notes',
                                                'upper': False,
                                                'html': ''},
                        'parent_mother': {'db_id': 'parent_mother__reg_no',
                                          'name': atatched_service.mother_title,
                                          'upper': True,
                                          'html': ''},
                        'parent_mother_notes': {'db_id': 'parent_mother_notes',
                                                'name': f'{atatched_service.mother_title} Notes',
                                                'upper': False,
                                                'html': ''},
                        'breed_group': {'db_id': 'breed_group__group_name',
                                        'name': 'Breed Group',
                                        'upper': False,
                                        'html': ''},
                        'breed': {'db_id': 'breed__breed_name',
                                  'name': 'Breed',
                                  'upper': False,
                                  'html': ''},
                        'coi': {'db_id': 'coi',
                                'name': 'COI',
                                'upper': False,
                                'html': ''},
                        'mean_kinship': {'db_id': 'mean_kinship',
                                         'name': 'Mean Kinship',
                                         'upper': False,
                                         'html': ''},
                        }

    site_columns = atatched_service.pedigree_columns.split(',')
    columns = []
    for column in site_columns:
        columns.append(pedigree_mapping[column]['db_id'])
    return columns, pedigree_mapping
