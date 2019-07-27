from django.contrib import admin
from .models import DatabaseUpload


class DatabaseUploadAdmin(admin.ModelAdmin):
    list_display = ('account', 'database', 'file_type')
    list_display_links = ['account']
    search_fields = ('account', 'database', 'file_type')
    list_filter = ('account', 'database', 'file_type')
    ordering = ['account']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(DatabaseUpload, DatabaseUploadAdmin)