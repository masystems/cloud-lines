from django.contrib import admin
from .models import DatabaseUpload, FileSlice, ExportQueue


class DatabaseUploadAdmin(admin.ModelAdmin):
    list_display = ('account', 'header')
    list_display_links = ['account']
    search_fields = ('account', 'header')
    list_filter = ('account', 'header')
    ordering = ['account']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(DatabaseUpload, DatabaseUploadAdmin)


class FileSliceAdmin(admin.ModelAdmin):
    list_display = ('database_upload', 'file_type')
    list_display_links = ['database_upload']
    search_fields = ('database_upload', 'file_type')
    list_filter = ('database_upload', 'file_type')
    ordering = ['database_upload']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(FileSlice, FileSliceAdmin)


class ExportAdmin(admin.ModelAdmin):
    list_display = ('account', 'user', 'file_name', 'complete', 'download_url', 'created')
    list_display_links = ['account', 'user', 'file_name', 'complete', 'download_url', 'created']
    search_fields = ('account', 'user', 'file_name', 'complete', 'download_url', 'created')
    list_filter = ('account', 'user', 'file_name', 'complete', 'download_url', 'created')
    ordering = ['account', 'user', 'file_name', 'complete', 'download_url', 'created']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(ExportQueue, ExportAdmin)