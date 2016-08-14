from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.conf.urls import url
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserCreationForm
from django.utils.module_loading import import_string
from django.shortcuts import render, redirect
from . import models
from . import es
from . import uploads


class HooverAdminSite(admin.AdminSite):

    pass


class CollectionAdminForm(forms.ModelForm):

    loader = forms.ChoiceField(choices=[
        (import_name, import_string(import_name).label)
        for import_name in settings.HOOVER_LOADERS
    ])


class CollectionAdmin(admin.ModelAdmin):

    list_display = ['__unicode__', 'count', 'access_list', 'public', 'upload']

    form = CollectionAdminForm

    def get_prepopulated_fields(self, request, obj=None):
        return {} if obj else {'name': ['title']}

    def get_readonly_fields(self, request, obj=None):
        return ['name'] if obj else []

    def upload(self, obj):
        if obj.loader == 'collector.loaders.upload.Loader':
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

class HooverUserCreateForm(UserCreationForm):

    send_email = forms.BooleanField()
    email = forms.EmailField(label="Email", required=True, max_length=254)

    def save(self, *args, **kwargs):
        user = super(HooverUserCreateForm, self).save(*args, **kwargs)

        if self.cleaned_data['send_email']:
            message = (
                "Your username is '{}' and the password is '{}'."
                .format(user.username, self.cleaned_data['password1'])
            )
            send_mail(
                subject="Welcome to Hoover",
                message=message,
                from_email=None,
                recipient_list=[user.email],
            )

        return user

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'send_email']


class HooverUserAdmin(UserAdmin):

    add_form = HooverUserCreateForm
    prepopulated_fields = {'username': ['first_name', 'last_name']}
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': [
                'first_name',
                'last_name',
                'username',
                'email',
                'password1',
                'password2',
                'send_email',
            ],
        }),
    ]


admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection, CollectionAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(User, HooverUserAdmin)
