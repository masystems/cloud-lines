from .models import Pedigree


def get_pedigree_column_headings():
    # get pedigree model headings
    forbidden_pedigree_fields = ['id', 'creator', 'account', 'date_added', 'state', 'custom_fields']
    return [field for field in Pedigree._meta.get_fields(include_parents=False, include_hidden=False) if
                         field.name not in forbidden_pedigree_fields]


def get_site_pedigree_column_headings(atatched_service):
    pedigree_mapping = {'breeder': {'db_id': 'breeder__breeder_prefix',
                                    'name': 'Breeder'},
                        'current_owner': {'db_id': 'current_owner__breeder_prefix',
                                          'name': 'Current Owner'},
                        'reg_no': {'db_id': 'reg_no',
                                   'name': 'Reg No.'},
                        'tag_no': {'db_id': 'tag_no',
                                   'name': 'Tag No.'},
                        'name': {'db_id': 'name',
                                 'name': 'Name'},
                        'description': {'db_id': 'description',
                                        'name': 'Name'},
                        'date_of_registration': {'db_id': 'date_of_registration',
                                                 'name': 'Date of Registration'},
                        'dob': {'db_id': 'dob',
                                'name': 'Date of Birth'},
                        'dod': {'db_id': 'dod',
                                'name': 'Date of Birth'},
                        'status': {'db_id': 'status',
                                   'name': 'Status'},
                        'sex': {'db_id': 'sex',
                                'name': 'Sex',
                                'html': """<span class="label label-primary"> %REPLACEME% </span>"""},
                        'parent_father': {'db_id': 'parent_father__reg_no',
                                          'name': atatched_service.father_title},
                        'parent_father_notes': {'db_id': 'parent_father_notes',
                                                'name': f'{atatched_service.father_title} Notes'},
                        'parent_mother': {'db_id': 'parent_mother__reg_no',
                                          'name': atatched_service.mother_title},
                        'parent_mother_notes': {'db_id': 'parent_mother_notes',
                                                'name': f'{atatched_service.mother_title} Notes'},
                        'breed_group': {'db_id': 'breed_group__group_name',
                                        'name': 'Breed Group'},
                        'breed': {'db_id': 'breed__breed_name',
                                  'name': 'Breed'},
                        'coi': {'db_id': 'coi',
                                'name': 'COI'},
                        'mean_kinship': {'db_id': 'mean_kinship',
                                         'name': 'Mean Kinship'},
                        }

    site_columns = atatched_service.pedigree_columns.split(',')
    columns = []
    for column in site_columns:
        columns.append(pedigree_mapping[column]['db_id'])
    return columns, pedigree_mapping
