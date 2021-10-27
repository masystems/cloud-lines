from django.contrib import admin
from .models import BreedGroup


class BreedGroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'account', 'breeder', 'breed')
    list_display_links = ['group_name']
    search_fields = ('group_name', 'account', 'breeder', 'breed')
    list_filter = ('group_name', 'account', 'breeder', 'breed')
    ordering = ['group_name']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(BreedGroup, BreedGroupAdmin)