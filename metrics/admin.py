from django.contrib import admin
from .models import CoiLastRun, MeanKinshipLastRun, KinshipQueue, StudAdvisorQueue, DataValidatorQueue


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


class KinshipAdmin(admin.ModelAdmin):
    list_display = ('account', 'user', 'file')
    list_display_links = ['account']
    list_filter = ('account', 'user', 'file')
    search_fields = ['account', 'user', 'file']
    ordering = ['account']
    empty_value_display = '-empty-'

admin.site.register(KinshipQueue, KinshipAdmin)


class StudAdvisorAdmin(admin.ModelAdmin):
    list_display = ('account', 'user', 'file')
    list_display_links = ['account']
    list_filter = ('account', 'user', 'file')
    search_fields = ['account', 'user', 'file']
    ordering = ['account']
    empty_value_display = '-empty-'

admin.site.register(StudAdvisorQueue, StudAdvisorAdmin)


class DataValidatorAdmin(admin.ModelAdmin):
    list_display = ('account', 'user', 'result')
    list_display_links = ['account']
    list_filter = ('account', 'user', 'result')
    search_fields = ['account', 'user', 'result']
    ordering = ['account']
    empty_value_display = '-empty-'

admin.site.register(DataValidatorQueue, DataValidatorAdmin)