from django.contrib import admin
from . import models

admin.site.register(models.Collection, admin.ModelAdmin)
admin.site.register(models.Document, admin.ModelAdmin)
