from django.contrib import admin
from .models import Pedigree, PedigreeImage


class PedigreeImagesInline(admin.TabularInline):
    model = PedigreeImage


class PedigreeAdmin(admin.ModelAdmin):
    list_display = ('account', 'creator', 'reg_no', 'name', 'breeder')
    list_display_links = ['account']
    list_filter = ('account', 'creator', 'date_of_registration', 'breeder', 'current_owner', 'date_added')
    search_fields = ['account', 'creator', 'reg_no', 'name', 'breeder', 'current_owner', 'date_added']
    ordering = ['account']
    empty_value_display = '-empty-'

    save_on_top = True
    inlines = [PedigreeImagesInline]


admin.site.register(Pedigree, PedigreeAdmin)
