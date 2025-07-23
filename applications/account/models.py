from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# For some extensions to these fields look at forms.py
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
        default='en',
        blank=True,
    )  # could be with dialects

    is_bot =  models.BooleanField(
        max_length=16,
        verbose_name='Is Bot',
        null=True,
        blank=True,
    )

    raw_data = models.JSONField(
        verbose_name='Raw Telegram User data',
        default=dict,
        null=True,
        blank=True,
    )

    description = models.TextField(
        max_length=700,
        verbose_name='Description',
        blank=True,
        null=True,
        help_text='You can describe yourself and add contacts here.'
    )

    specialisation = models.TextField(
        max_length=40,
        verbose_name='Specialisation',
        blank=True,
        null=True,
        help_text='What is your superpower? What do you do best?'
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f"User: {self.username}, {self.telegram_username or '***'}"
    
class MapMarker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='map_markers')
    latitude = models.FloatField(
        verbose_name='Latitude center of the map',
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        blank=True,
        null=True,
    )
    longitude = models.FloatField(
        verbose_name='Longitude center of the map',
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
