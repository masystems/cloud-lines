from django.contrib import admin
from .models import SiteDetail, UserDetail, Service



class UserServicesInline(admin.TabularInline):
    model = Service
    extra = 3


class UserDetailAdmin(admin.ModelAdmin):
    inlines = [UserServicesInline]


admin.site.register(SiteDetail)

admin.site.register(UserDetail, UserDetailAdmin)