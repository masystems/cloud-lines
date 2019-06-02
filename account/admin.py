from django.contrib import admin
from .models import SiteDetail, UserDetail, AttachedService



class UserServicesInline(admin.TabularInline):
    model = AttachedService
    extra = 3


class UserDetailAdmin(admin.ModelAdmin):
    inlines = [UserServicesInline]


admin.site.register(SiteDetail)

admin.site.register(UserDetail, UserDetailAdmin)