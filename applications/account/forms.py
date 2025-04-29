from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from . import models

User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = [
            'first_name',
            'last_name',
            'telegram_language',
            'latitude_center',
            'longitude_center',
            'map_zoom',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].label = _('First name')
        self.fields['last_name'].label = _('Last name')
        self.fields['telegram_language'].label = _('Telegram language')
        self.fields['latitude_center'].label = _('Latitude of map center')
        self.fields['longitude_center'].label = _('Longitude of map center')
        self.fields['map_zoom'].label = _('Map zoom')
