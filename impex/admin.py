from django.contrib import admin
from .models import DatabaseUpload, FileSlice


class DatabaseUploadAdmin(admin.ModelAdmin):
    list_display = ('account', 'created', 'user')
    list_display_links = ['account']
    search_fields = ('account', 'created', 'user')
    list_filter = ('account', 'created', 'user')
    ordering = ['created']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(DatabaseUpload, DatabaseUploadAdmin)


class FileSliceAdmin(admin.ModelAdmin):
    list_display = ('slice_number', 'database_upload')
    list_display_links = ['slice_number']
    search_fields = ('slice_number', 'database_upload')
    list_filter = ('slice_number', 'database_upload')
    ordering = ['slice_number']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(FileSlice, FileSliceAdmin)