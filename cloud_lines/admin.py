from django.contrib import admin
from .models import Service, Bolton, Page, Gallery, Faq, Contact, Testimonial, LargeTierQueue, Blog, Update


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('ordering', 'service_name', 'admin_users', 'contrib_users', 'read_only_users', 'number_of_animals', 'multi_breed', 'support', 'price_per_month', 'price_per_year')
    list_display_links = ['service_name']
    ordering = ['ordering']
    empty_value_display = '-empty-'

    save_on_top = True


class BoltonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    list_display_links = ['name']
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ['name']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(Bolton, BoltonAdmin)
admin.site.register(LargeTierQueue)
admin.site.register(Service, ServicesAdmin)
admin.site.register(Gallery)
admin.site.register(Page)
admin.site.register(Faq)
admin.site.register(Contact)
admin.site.register(Testimonial)
admin.site.register(Blog)
admin.site.register(Update)
