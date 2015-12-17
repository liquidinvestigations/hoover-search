from django import forms
from django.core.mail import send_mail
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from . import models
from . import es


class HooverAdminSite(admin.AdminSite):

    index_template = 'admin-index.html'

    def get_urls(self):
        return [
            url(r'^es/$', self.admin_view(self.es_index), name='esindex'),
            url(r'^es/delete$', self.admin_view(self.es_delete)),
        ] + super(HooverAdminSite, self).get_urls()

    def es_index(self, request):
        return render(request, 'admin-es-index.html', {'stats': es.stats()})

    def es_delete(self, request):
        es.delete(request.POST['collection'])
        return redirect('.')


class CollectionAdmin(admin.ModelAdmin):

    list_display = ['__unicode__', 'count', 'public', 'access_list']

    def get_prepopulated_fields(self, request, obj=None):
        return {} if obj else {'slug': ['title']}

    def get_readonly_fields(self, request, obj=None):
        return ['slug'] if obj else []

class HooverUserCreateForm(UserCreationForm):

    send_email = forms.BooleanField()
    email = forms.EmailField(label="Email", required=True, max_length=254)

    def save(self, *args, **kwargs):
        user = super(HooverUserCreateForm, self).save(*args, **kwargs)
        print self.cleaned_data

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
