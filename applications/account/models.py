import logging
import json
import datetime
import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    '''
    Users: telegram users and other users
    '''

    telegram_id = models.BigIntegerField(
        verbose_name='Telegram ID',
        blank=True,
        null=True,
    )

    telegram_username = models.CharField(
        verbose_name='Telegram username',
        max_length=100,
        blank=True,
    )

    telegram_language = models.CharField(
        verbose_name='Language',
        max_length=16,
        # default='en',
        blank=True,
    )  # could be with dialects

    is_bot =  models.BooleanField(
        max_length=16,
        verbose_name='Is Bot',
        blank=True,
    )

    raw_data = models.JSONField(
        verbose_name='Raw Telegram User data',
        default=dict,
        null=True,
        blank=True,
    )

    latitude_center = models.FloatField(
        verbose_name='Latitude center of the map',
        blank=True,
        null=True,
    )

    longitude_center = models.FloatField(
        verbose_name='Longitude center of the map',
        blank=True,
        null=True,
    )

    map_zoom = models.PositiveSmallIntegerField(
        verbose_name='Zoom of the map',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f"User: {self.username}, {self.telegram_username or '***'}"
