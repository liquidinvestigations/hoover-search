from django import forms
from django.shortcuts import get_object_or_404
from django.conf.urls import url
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.utils.module_loading import import_string
from django.shortcuts import render
from ..contrib import installed
from . import models
from . import uploads

if installed.twofactor:
    from django_otp.admin import OTPAdminSite
    _admin_baseclass = OTPAdminSite
else:
    _admin_baseclass = admin.AdminSite


class HooverAdminSite(_admin_baseclass):

    pass


class CollectionAdminForm(forms.ModelForm):

    loader = forms.ChoiceField(choices=[
        (import_name, import_string(import_name).label)
        for import_name in settings.HOOVER_LOADERS
    ])


class CollectionAdmin(admin.ModelAdmin):

    list_display = ['__str__', 'count', 'access_list', 'public', 'upload']
    fields = ['title', 'name', 'index', 'public', 'users', 'loader', 'options']
    filter_horizontal = ['users']

    form = CollectionAdminForm

    def get_prepopulated_fields(self, request, obj=None):
        return {} if obj else {'name': ['title'], 'index': ['name']}

    def upload(self, obj):
        if obj.loader == 'hoover.search.loaders.upload.Loader':
            return '<a href="%s/upload">upload</a>' % obj.pk

    upload.allow_tags = True

    def upload_view(self, request, pk):
        collection = get_object_or_404(models.Collection, pk=pk)

        if request.method == 'POST':
            results = uploads.handle_zipfile(
                request,
                collection,
                request.FILES['file'],
            )
            return render(request, 'admin-upload-results.html', {
                'collection': collection,
                'results': results
            })

        return render(request, 'admin-upload.html', {'collection': collection})

    def get_urls(self):
        return [
            url(r'^(.+)/upload$', self.admin_site.admin_view(self.upload_view)),
        ] + super(CollectionAdmin, self).get_urls()

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.rel.to == get_user_model():
            field.label_from_instance = self.get_user_label
        return field

    def get_user_label(self, user):
        name = user.get_full_name()
        username = user.username
        if name and name != username:
            return "{} ({})".format(username, name)
        else:
            return username


class HooverUserAdmin(UserAdmin):
    actions = []


admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection, CollectionAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(User, HooverUserAdmin)
