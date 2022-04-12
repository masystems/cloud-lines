from django.contrib import admin
from cloud_lines.models import Bolton


class BoltonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    list_display_links = ['name']
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ['name']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(Bolton, BoltonAdmin)