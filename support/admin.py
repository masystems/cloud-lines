from django.contrib import admin
from .models import Ticket

class SupportAdmin(admin.ModelAdmin):
    list_display = ('account', 'user', 'date_time', 'subject', 'priority', 'status')
    list_display_links = ['account']
    search_fields = ('account', 'user', 'date_time', 'subject', 'priority', 'status')
    list_filter = ('account', 'user', 'date_time', 'subject', 'priority', 'status')
    ordering = ['date_time']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(Ticket, SupportAdmin)