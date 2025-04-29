import math

from django.contrib import admin
from django.utils.html import mark_safe

from applications.core.admin import CommonAdmin
from . import models


@admin.register(models.Marker)
class MarkerAdmin(CommonAdmin):
    list_display = ['id', 'user', 'status', 'thumb_photo', 'time']
    list_filter = ['status']
    readonly_fields = ['thumb_photo', 'resize_photo', 'created', 'modified', 'time']
    fieldsets = (
        (None, {
            'fields': (
                'status',
                'user',
                'time',
                ('latitude', 'longitude'),
                'message',
            )
        }),
        ('Photo', {
            'fields': ('resize_photo', 'photo',)
        }),
        ('Created / Modified', {
            'fields': ('created', 'modified',)
        }),
    )

    def thumb_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100">')
        return '-' * 10
    thumb_photo.short_description = 'Preview'

    def resize_photo(self, obj):
        if obj.photo:
            width = obj.photo.width
            height = obj.photo.height
            max_size = max(width, height)
            if max_size > 600:
                proportion_side = math.ceil(max_size / 600)
                width = width / proportion_side
                height = height / proportion_side
            return mark_safe(f'<img src="{obj.photo.url}" width="{width}" height={height} />')
        return None
    resize_photo.short_description = 'Photo'
