from django.contrib import admin

from .models import Breeder

class BreederAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    list_display_links = ('prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    search_fields = ('prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    list_filter = ('active', 'prefix')
    ordering = ['prefix']
    empty_value_display = '-empty-'

    fieldsets = (
        ('Attached Site', {
            'fields': ('account',)
        }),
        ('Breeder details', {
            'fields': ('prefix', 'active')
        }),
        ('Contact options', {
            'fields': ('contact_name', 'address', 'phone_number1', 'phone_number2', 'email', 'custom_fields'),
        }),
    )
    save_on_top = True


admin.site.register(Breeder, BreederAdmin)