from django import forms
from django.contrib import admin
from django.contrib.admin import action
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.forms import ModelForm
from . import models


class HooverAdminSite(admin.AdminSite):
    pass


class CollectionCreateForm(forms.ModelForm):

    class Meta:
        fields = ['name', 'title']
        model = models.Collection


class CollectionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'count', 'user_access_list', 'group_access_list',
                    'uploaders_access_list', 'group_upload_access_list',
                    'group_access_list', 'public', 'writeable', 'avg_search_time',
                    'avg_batch_time',
                    'process', 'progress', 'sync']
    filter_horizontal = ['users', 'groups', 'uploader_users', 'uploader_groups']
    actions = [
        'make_collection_writeable',
        'make_collection_not_writeable',
        'make_collection_public',
        'make_collection_not_public',
        'enable_collection_process',
        'disable_collection_process',
        "enable_collection_sync",
        "disable_collection_sync",
    ]

    @action(description='Set collections as Public')
    def make_collection_public(self, request, queryset):
        queryset.update(public=True)

    @action(description='Set collections as Not Public')
    def make_collection_not_public(self, request, queryset):
        queryset.update(public=False)

    @action(description='Set collections as Writeable')
    def make_collection_writeable(self, request, queryset):
        queryset.update(writeable=True)

    @action(description='Set collections as Not Writeable')
    def make_collection_not_writeable(self, request, queryset):
        queryset.update(writeable=False)

    @action(description='Enable processing for collections')
    def enable_collection_process(self, request, queryset):
        for item in queryset:
            item.config['process'] = True
            item.save()

    @action(description='Disable processing for collections')
    def disable_collection_process(self, request, queryset):
        for item in queryset:
            item.config['process'] = False
            item.save()

    @action(description='Enable Sync for collections')
    def enable_collection_sync(self, request, queryset):
        for item in queryset:
            item.config['sync'] = True
            item.save()

    @action(description='Disable Sync for collections')
    def disable_collection_sync(self, request, queryset):
        for item in queryset:
            item.config['sync'] = False
            item.save()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['name', 'index', 'process', 'progress', 'sync', 'config', 'stats']
        else:
            return ['index']

    def get_fields(self, request, obj=None):
        if obj:
            return [
                'name', 'index', 'title',
                'public', 'writeable',
                'users', 'groups',
                'uploader_users', 'uploader_groups',
                'process', 'progress', 'sync',
                'config',
            ]
        else:
            return ['name', 'title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        qs_user = qs.filter(users__in=[request.user.id])
        qs_groups = qs.filter(groups__in=request.user.groups.all())
        return qs_user | qs_groups

    # def get_prepopulated_fields(self, request, obj=None):
    #     return {} if obj else {'name': ['title'], 'index': ['name']}

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'users':
            field.label_from_instance = self.get_user_label
        return field

    def count(self, collection):
        return collection.count

    def progress(self, collection):
        return collection.stats.get('progress_str')

    def get_user_label(self, user):
        name = user.get_full_name()
        username = user.username
        if name and name != username:
            return "{} ({})".format(username, name)
        else:
            return username

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            print('collection add form', str(obj), str(kwargs))
            kwargs['form'] = CollectionCreateForm
        else:
            print('collection edit form', str(obj))
        return super().get_form(request, obj, **kwargs)

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class GroupAdminForm(ModelForm):
    class Meta:
        model = Group
        exclude = []

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()
        return instance


class HooverGroupAdmin(GroupAdmin):
    form = GroupAdminForm
    fields = ['name', 'users']
    exclude = ['permissions']


class ProfileInline(admin.StackedInline):
    model = models.Profile
    can_delete = False
    verbose_name_plural = 'profile'
    fields = ('user', 'uuid', 'preferences')
    readonly_fields = ('user', 'uuid', 'preferences')
    list_display = ('user', 'uuid', 'preferences')


class HooverUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    actions = []
    fieldsets = (
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = [
        'first_name', 'last_name', 'email',
        'last_login', 'date_joined', 'username',  # 'password',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


# class HooverSearchResultCacheAdmin(admin.ModelAdmin):
#     readonly_fields = ['args_size', 'user', 'collections', 'result_size', 'task_id', 'date_started', 'date_finished',
#                        'args', 'result', 'txt_query', 'result_hits', 'result_agg_hits']
#     fields = readonly_fields
#     list_display = ['task_id', 'user', 'str_collections', 'date_started', 'date_finished', 'args_size', 'result_size',
#                     'txt_query', 'result_hits', 'result_agg_hits']
#
#     def len_collections(self, item):
#         return len(item.collections)
#
#     def str_collections(self, item):
#         _str = ', '.join(c.name for c in item.collections.all())
#         _str = f'{len(item.collections.all())} items: ' + _str
#         if len(_str) > 40:
#             _str = _str[:37] + '...'
#         return _str
#
#     def args_size(self, item):
#         return len(str(item.args))
#
#     def result_size(self, item):
#         return len(str(item.result))
#
#     def txt_query(self, item):
#         return item.args.get('query', {}).get('query_string', {}).get('query')
#
#     def result_hits(self, item):
#         return len(item.result.get('hits', {}).get('hits', []))
#
#     def result_agg_hits(self, item):
#         return len((item.result or {}).get('aggregations', [])) or None
#
#
# class HooverBatchSearchResultCacheAdmin(admin.ModelAdmin):
#     readonly_fields = ['args_size', 'user', 'collections', 'result_size', 'task_id', 'date_started', 'date_finished',
#                        'args', 'result', 'the_query_strings', 'result_hits']
#     fields = readonly_fields
#     list_display = ['task_id', 'user', 'str_collections', 'date_started', 'date_finished', 'args_size', 'result_size',
#                     'the_query_strings', 'result_hits']
#
#     def len_collections(self, item):
#         return len(item.collections)
#
#     def str_collections(self, item):
#         _str = ', '.join(c.name for c in item.collections.all())
#         _str = f'{len(item.collections.all())} items: ' + _str
#         if len(_str) > 40:
#             _str = _str[:37] + '...'
#         return _str
#
#     def args_size(self, item):
#         return len(str(item.args))
#
#     def result_size(self, item):
#         return len(str(item.result))
#
#     def the_query_strings(self, item):
#         _str = ', '.join(item.args.get('query_strings', []))
#         _len = len(item.args.get('query_strings', []))
#         if len(_str) > 40:
#             _str = _str[:37] + '...'
#         _str = str(_len) + ' items: ' + _str
#         return _str
#
#     def result_hits(self, item):
#         results = [x.get('hits', {}).get('total', 0)
#                    for x in (item.result or {}).get('responses', [])]
#         result_count = sum(results)
#         first_results = results[:10]
#         _str = f'{result_count} = {" + ".join(map(str, first_results))}'
#         if len(_str) > 40:
#             _str = _str[:37] + '...'
#         return _str


admin_site = HooverAdminSite(name='hoover-admin')
admin_site.register(models.Collection, CollectionAdmin)
admin_site.register(Group, HooverGroupAdmin)
admin_site.register(User, HooverUserAdmin)

# admin_site.register(models.SearchResultCache, HooverSearchResultCacheAdmin)
# admin_site.register(models.BatchResultCache, HooverBatchSearchResultCacheAdmin)

admin_site.site_header = 'Hoover Search Administration'
