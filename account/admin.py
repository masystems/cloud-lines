from django.contrib import admin
from .models import UserDetail, AttachedService



class UserServicesInline(admin.StackedInline):
    model = AttachedService


class UserDetailAdmin(admin.ModelAdmin):
    inlines = [UserServicesInline]


admin.site.register(UserDetail, UserDetailAdmin)
admin.site.register(AttachedService)