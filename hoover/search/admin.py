from django import forms
from django.db import transaction
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import User, Group, UserAdmin, GroupAdmin
from django.forms import ModelForm
from django.urls import reverse
from django.utils.html import format_html
from . import models


class HooverAdminSite(admin.AdminSite):
    pass


class CollectionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'count', 'user_access_list', 'group_access_list',
                    'uploaders_access_list', 'group_upload_access_list',
                    'group_access_list', 'public', 'writeable', 'avg_search_time', 'avg_batch_time',
                    'link_to_nccollection']
    fields = ['title', 'name', 'index', 'public', 'writeable', 'users', 'groups', 'uploader_users', 'uploader_groups']
    filter_horizontal = ['users', 'groups', 'uploader_users', 'uploader_groups']
    readonly_fields = ['index', 'name']

    def link_to_nccollection(self, obj):
        nc_collection = obj.nextcloudcollection_set.first()
        if nc_collection:
            link = reverse("admin:search_nextcloudcollection_change", args=[nc_collection.id])
            return format_html(f'<a href="{link}"><b>{nc_collection}</b></a>')
        else:
            return None

    link_to_nccollection.short_description = 'Nextcloud Collection'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        qs_user = qs.filter(users__in=[request.user.id])
        qs_groups = qs.filter(groups__in=request.user.groups.all())
        return qs_user | qs_groups

    def get_prepopulated_fields(self, request, obj=None):
        return {} if obj else {'name': ['title'], 'index': ['name']}

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'users':
            field.label_from_instance = self.get_user_label
        return field

    def count(self, collection):
        return collection.count

    def get_user_label(self, user):
        name = user.get_full_name()
        username = user.username
        if name and name != username:
            return "{} ({})".format(username, name)
        else:
            return username

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class NextcloudDirectoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'path', 'user', 'exists_in_nextcloud', 'deleted_from_nextcloud', 'link_to_nccollection']
    search_fields = ['path']
    readonly_fields = ['name', 'path', 'modified', 'user', 'deleted_from_nextcloud']

    def link_to_nccollection(self, obj):
        link = reverse("admin:search_nextcloudcollection_change", args=[obj.nextcloudcollection.id])
        return format_html(f'<a href="{link}"><b>{obj.nextcloudcollection}</b></a>')

    link_to_nccollection.short_description = 'Nextcloud Collection'

    def exists_in_nextcloud(self, obj):
        return False if obj.deleted_from_nextcloud else True

    exists_in_nextcloud.boolean = True

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term,
        )
        # only filter the deleted directories in the autocomplete dialougue
        # but not in the list display
        if 'autocomplete' in request.get_full_path():
            queryset = queryset.filter(deleted_from_nextcloud__isnull=True)
        return queryset, may_have_duplicates

    def path(self, obj):
        return str(obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NextcloudCollectionForm(ModelForm):
    class Meta:
        model = models.NextcloudCollection
        fields = [
            'name',
            'directory',
            'process',
            'sync',
            'ocr_languages',
            'max_result_window',
            'pdf_preview_enabled',
            'thumbnail_generator_enabled',
            'image_classification_object_detection_enabled',
            'image_classification_classify_images_enabled',
            'nlp_language_detection_enabled',
            'nlp_fallback_language',
            'nlp_entity_extraction_enabled',
            'translation_enabled',
            'translation_target_languages',
            'translation_text_length_limit',
            'default_table_header',
            'explode_table_rows',
            's3_blobs_address',
            's3_blobs_access_key',
            's3_blobs_secret_key',
        ]


class NextcloudCollectionAdmin(admin.ModelAdmin):
    form = NextcloudCollectionForm
    autocomplete_fields = ['directory']
    list_display = [
        'name',
        'username',
        'link_to_collection'
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['name', 'directory']
        else:
            return []

    def link_to_collection(self, obj):
        link = reverse("admin:search_collection_change", args=[obj.collection.id])
        return format_html(f'<a href="{link}"><b>{obj.collection}</b></a>')

    link_to_collection.short_description = 'Collection'

    def username(self, obj):
        return obj.username

    def name(self, obj):
        return obj.name

    def password(self, obj):
        return obj.password

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            collection, _ = models.Collection.objects.get_or_create(name=obj.name, index=obj.name)
            obj.collection = collection
            super().save_model(request, obj, form, change)


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


class WebDAVPasswordInlineForm(ModelForm):
    class Meta:
        model = models.WebDAVPassword
        exclude = ['user']
        widgets = {
            'password': forms.PasswordInput(),
        }


class WebDAVPasswordInline(admin.StackedInline):  # You can use TabularInline as an alternative
    model = models.WebDAVPassword
    can_delete = False
    form = WebDAVPasswordInlineForm


class HooverUserAdmin(UserAdmin):
    inlines = (ProfileInline,
               WebDAVPasswordInline,)
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
admin_site.register(models.NextcloudCollection, NextcloudCollectionAdmin)
admin_site.register(models.NextcloudDirectory, NextcloudDirectoryAdmin)
admin_site.register(Group, HooverGroupAdmin)
admin_site.register(User, HooverUserAdmin)

# admin_site.register(models.SearchResultCache, HooverSearchResultCacheAdmin)
# admin_site.register(models.BatchResultCache, HooverBatchSearchResultCacheAdmin)

admin_site.site_header = 'Hoover Search Administration'
