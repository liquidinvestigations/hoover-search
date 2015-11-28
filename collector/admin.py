from django.conf.urls import url
from django.contrib.admin import AdminSite
from django.shortcuts import render, redirect
from . import models
from . import es


class HooverAdminSite(AdminSite):

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

admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection)


from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
