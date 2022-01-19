from django.contrib import admin
from .models import UserDetail, AttachedService, AttachedBolton


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
    list_display = ('user', 'service')
    list_display_links = ['user', 'service']
    search_fields = ('user', 'service')
    list_filter = ('user', 'service')

admin.site.register(AttachedService, AttachedServiceAdmin)


class AttachedBoltonAdmin(admin.ModelAdmin):
    list_display = ('bolton', 'stripe_sub_id', 'increment', 'active')
    list_display_links = ['bolton', 'stripe_sub_id', 'increment', 'active']
    search_fields = ('bolton', 'stripe_sub_id', 'increment', 'active')
    list_filter = ('bolton', 'stripe_sub_id', 'increment', 'active')
    ordering = ['bolton']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(AttachedBolton, AttachedBoltonAdmin)