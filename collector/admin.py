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
            url(r'^es/$', self.es_index, name='esindex'),
            url(r'^es/delete$', self.es_delete),
        ] + super(HooverAdminSite, self).get_urls()

    def es_index(self, request):
        return render(request, 'admin-es-index.html', {'stats': es.stats()})

    def es_delete(self, request):
        es.delete(request.POST['collection'])
        return redirect('.')


class CollectionAdmin(admin.ModelAdmin):

    list_display = ['__unicode__', 'count', 'public', 'access_list']


class HooverUserCreateForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


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
                'password1',
                'password2',
            ],
        }),
    ]


admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection, CollectionAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(User, HooverUserAdmin)
