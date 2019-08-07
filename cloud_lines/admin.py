from django.contrib import admin
from .models import Service, Page, Faq, Contact, Testimonial, LargeTierQueue


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('ordering', 'service_name', 'admin_users', 'read_only_users', 'number_of_animals', 'multi_breed', 'support', 'price_per_month', 'price_per_year')
    list_display_links = ['service_name']
    #list_filter = ('account', 'creator', 'date_of_registration', 'breeder', 'current_owner', 'date_added')
    #search_fields = ['account', 'creator', 'reg_no', 'name', 'breeder', 'current_owner', 'date_added']
    ordering = ['ordering']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(LargeTierQueue)
admin.site.register(Service, ServicesAdmin)
admin.site.register(Page)
admin.site.register(Faq)
admin.site.register(Contact)
admin.site.register(Testimonial)
