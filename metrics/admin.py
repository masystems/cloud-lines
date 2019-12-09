from django.contrib import admin
from .models import CoiLastRun, MeanKinshipLastRun


class CoiAdmin(admin.ModelAdmin):
    list_display = ('account', 'last_run')
    list_display_links = ['account']
    list_filter = ('account', 'last_run')
    search_fields = ['account', 'last_run']
    ordering = ['account']
    empty_value_display = '-empty-'


admin.site.register(CoiLastRun, CoiAdmin)


class MeaKinshipAdmin(admin.ModelAdmin):
    list_display = ('account', 'last_run')
    list_display_links = ['account']
    list_filter = ('account', 'last_run')
    search_fields = ['account', 'last_run']
    ordering = ['account']
    empty_value_display = '-empty-'


admin.site.register(MeanKinshipLastRun, MeaKinshipAdmin)