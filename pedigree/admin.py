from django.contrib import admin
from .models import Pedigree, PedigreeImage, PedigreeAttributes


class PedigreeAttributesInline(admin.StackedInline):
    model = PedigreeAttributes


class PedigreeImagesInline(admin.TabularInline):
    model = PedigreeImage


class PedigreeAdmin(admin.ModelAdmin):
    list_display = ('reg_no', 'name', 'breeder', 'note')
    list_display_links = ('name', 'breeder', 'reg_no')
    list_filter = ('date_of_registration', 'breeder', 'current_owner', 'date_added')
    search_fields = ['name', 'reg_no']
    ordering = ['reg_no']
    empty_value_display = '-empty-'
    fields = (('user', 'breeder', 'current_owner'),
              ('reg_no', 'name'),
              ('description',),
              ('date_of_registration',),
              ('dob',),
              ('dod',),
              'sex',
              ('parent_father', 'parent_mother', 'breed_group'),
              'note',)
    save_on_top = True
    inlines = [PedigreeAttributesInline, PedigreeImagesInline]


admin.site.register(Pedigree, PedigreeAdmin)
