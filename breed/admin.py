from django.contrib import admin
from .models import Breed

class BreedAdmin(admin.ModelAdmin):
    list_display = ('breed_name', 'account', 'breed_description')
    list_display_links = ['breed_name']
    search_fields = ('breed_name', 'account', 'breed_description')
    list_filter = ('breed_name', 'account', 'breed_description')
    ordering = ['breed_name']
    empty_value_display = '-empty-'

    save_on_top = True


admin.site.register(Breed, BreedAdmin)