from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from applications.core.models import Common, PathAndRename


class Marker(Common):
    '''
    Marker location on the map
    '''

    latitude = models.FloatField(
        verbose_name='Latitude',
    )

    longitude = models.FloatField(
        verbose_name='Longitude',
    )

    user = models.ForeignKey(
        verbose_name='User',
        to=get_user_model(),
        on_delete=models.SET_NULL,
        related_name='markers',
        limit_choices_to={"is_staff": False},
        null=True,
    )

    time = models.DateTimeField(
        verbose_name='Time',
        auto_now_add=True,
    )

    message = models.TextField(
        verbose_name='Message',
        blank=True,
    )

    photo = models.ImageField(
        verbose_name='Photo',
        upload_to=PathAndRename('map/marker/photo'),
        help_text='Max size 800x800px. JPG',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'marker'
        verbose_name_plural = 'markers'

    def __str__(self):
        return f'{self.time}, {self.latitude}, {self.longitude}'
