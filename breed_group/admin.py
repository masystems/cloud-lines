from django.contrib import admin
from .models import BreedGroup


class BreedGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'account', 'breeder', 'breed')
    list_display_links = ['group_id']
    search_fields = ('group_id', 'account', 'breeder', 'breed')
    list_filter = ('group_id', 'account', 'breeder', 'breed')
    ordering = ['group_id']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(BreedGroup, BreedGroupAdmin)