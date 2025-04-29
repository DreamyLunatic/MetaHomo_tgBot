import math

from django.contrib import admin
# from .models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe
from django_admin_inline_paginator.admin import TabularInlinePaginated

from applications.map.models import Marker

User = get_user_model()


# class MarkerInline(admin.StackedInline):
# class MarkerInline(admin.TabularInline):
class MarkerInline(TabularInlinePaginated):
    model = Marker
    per_page = 2
    extra = 0
    fields = ['status', 'time', 'message', 'thumb_photo']
    readonly_fields = ['status', 'time', 'message', 'thumb_photo']
    can_delete = False
    show_change_link = True

    def thumb_photo(self, obj):
        if obj.photo:
            width = obj.photo.width
            height = obj.photo.height
            max_size = max(width, height)
            if max_size > 100:
                proportion_side = math.ceil(max_size / 100)
                width = width / proportion_side
                height = height / proportion_side
            return mark_safe(f'<img src="{obj.photo.url}" width="{width}" height={height} />')
        return '-' * 10
    thumb_photo.short_description = 'Preview'

    def has_add_permission(self, request, obj=None):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return True

    # def has_delete_permission(self, request, obj=None):
    #     return True


@admin.register(User)
class AdminUser(UserAdmin):
    list_display = ['username', 'id', 'telegram_id', 'telegram_username', 'is_active', 'is_bot']
    list_filter = ['is_active', 'is_bot']
    search_fields = ['username', 'first_name', 'last_name', 'telegram_username']
    date_hierarchy = 'date_joined'
    ordering = ['-id']
    inlines = [MarkerInline]
    fieldsets = (
        (None, {
            'fields': ('username', 'password',)
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields':
                ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined',),
        }),
        ('Telegram data', {
            'fields': ('telegram_id', 'telegram_username', 'telegram_language', 'is_bot', 'raw_data'),
        }),
        ('Coordinates of the center of the visible map', {
            'fields': ('latitude_center', 'longitude_center', 'map_zoom'),
        }),
    )
