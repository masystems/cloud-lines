from .models import Pedigree

def get_all_pedigrees(attached_service, sort_by_col, start, end,
        search="", reg_no_search="", tag_no_search="", name_search="", desc_search="", dor_search="",
        dob_search="", dod_search="", status_search="", sex_search="", litter_search="",
        parent_father_search="", parent_father_notes_search="", parent_mother_search="", parent_mother_notes_search="",
        breed_search=""):

    # reg_no, name, litter_size, sale_or_hire - none of these can be None - the rest of the filterable fields can
    
    all_pedigrees = Pedigree.objects.filter(account=attached_service).order_by(sort_by_col).distinct()[
                            start:start + end]
    
    return all_pedigrees