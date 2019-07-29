from django.contrib import admin
from .models import Service, Page, Faq, Contact, Testimonial, LargeTierQueue


admin.site.register(LargeTierQueue)
admin.site.register(Service)
admin.site.register(Page)
admin.site.register(Faq)
admin.site.register(Contact)
admin.site.register(Testimonial)
