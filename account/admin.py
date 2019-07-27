from django.contrib import admin
from .models import UserDetail, AttachedService


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
admin.site.register(AttachedService)
