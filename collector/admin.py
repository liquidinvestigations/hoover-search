from django.contrib.admin import AdminSite
from . import models


class HooverAdminSite(AdminSite):

    index_template = 'admin-index.html'

admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection)


from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
