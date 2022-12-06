from django.contrib import admin
from .models import UserDetail, AttachedService, AttachedBolton, StripeAccount


class UserServicesInline(admin.StackedInline):
    model = AttachedService


class UserDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'stripe_id', 'current_service')
    list_display_links = ['user']
    search_fields = ('user', 'phone', 'stripe_id', 'current_service')
    list_filter = ('user', 'phone', 'stripe_id', 'current_service')
    ordering = ['user']
    empty_value_display = '-empty-'

    save_on_top = True

    inlines = [UserServicesInline]


admin.site.register(UserDetail, UserDetailAdmin)


class AttachedServiceAdmin(admin.ModelAdmin):
    list_display = ('organisation_or_society_name', 'user', 'service', 'domain', 'site_mode', 'active')
    list_display_links = ['organisation_or_society_name', 'user', 'service', 'domain', 'site_mode', 'active']
    search_fields = ('organisation_or_society_name', 'user', 'service', 'domain', 'site_mode', 'active')
    list_filter = ('organisation_or_society_name', 'user', 'service', 'domain', 'site_mode', 'active')

admin.site.register(AttachedService, AttachedServiceAdmin)


class AttachedBoltonAdmin(admin.ModelAdmin):
    list_display = ('bolton_name', 'active')
    list_display_links = ['bolton_name', 'active']
    search_fields = ('bolton', 'active')
    list_filter = ('bolton', 'active')
    ordering = ['bolton']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(AttachedBolton, AttachedBoltonAdmin)

admin.site.register(StripeAccount)