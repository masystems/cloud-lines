from django.contrib import admin

from .models import Breeder

class BreederAdmin(admin.ModelAdmin):
    list_display = ('account', 'breeding_prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    list_display_links = ('breeding_prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    search_fields = ('breeding_prefix', 'contact_name', 'address', 'phone_number1', 'phone_number2', 'email')
    list_filter = ('account', 'active', 'breeding_prefix')
    ordering = ['breeding_prefix']
    empty_value_display = '-empty-'

    fieldsets = (
        ('Attached Site', {
            'fields': ('account',)
        }),
        ('Breeder details', {
            'fields': ('breeding_prefix', 'active')
        }),
        ('Contact options', {
            'fields': ('contact_name', 'address', 'phone_number1', 'phone_number2', 'email', 'custom_fields'),
        }),
    )
    save_on_top = True


admin.site.register(Breeder, BreederAdmin)