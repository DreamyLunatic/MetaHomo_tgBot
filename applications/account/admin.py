from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from .models import User
from applications.account.models import MapMarker

admin.site.unregister(Group)

# ✏️ Кастомная форма изменения пользователя
class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔎 Оставляем только нужные разрешения
        allowed_codenames = [
            'add_user', 'change_user', 'delete_user', 'view_user',
            'add_mapmarker', 'change_mapmarker', 'delete_mapmarker', 'view_mapmarker',
        ]

        self.fields['user_permissions'].queryset = Permission.objects.filter(codename__in=allowed_codenames)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm  # подключаем кастомную форму

    list_display = ('username', 'telegram_username', 'telegram_language', 'is_bot', 'email', 'first_name', 'last_name')
    list_filter = ('is_bot', 'telegram_language')
    search_fields = ('username', 'telegram_username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username',)}),

        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'description', 'specialisation')}),

        (_('Telegram info'), {'fields': (
            'telegram_id',
            'telegram_username',
            'telegram_language',
            'is_bot',
            'raw_data',
        )}),

        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'user_permissions'),
        }),

        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            return readonly + ('is_superuser',)
        return readonly

    def save_model(self, request, obj, form, change):
        if change and not request.user.is_superuser:
            old_obj = type(obj).objects.get(pk=obj.pk)
            obj.is_superuser = old_obj.is_superuser
        super().save_model(request, obj, form, change)


@admin.register(MapMarker)
class MapMarkerAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude')
    search_fields = ('user__username',)
