from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import MapMarker, User

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'telegram_id',
            'telegram_username',
            'telegram_language',
            'is_bot',
            'description',
            'specialisation',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_language = getattr(self.instance, 'telegram_language', None)

        translations = {
            'ru': {
                'labels': {
                    'username': 'Имя пользователя',
                    'email': 'Электронная почта',
                    'telegram_id': 'Telegram ID',
                    'telegram_username': 'Telegram имя пользователя',
                    'is_bot': 'Это бот?',
                    'first_name': 'Имя',
                    'last_name': 'Фамилия',
                    'telegram_language': 'Язык Telegram',
                    'description': 'Описание',
                    'specialisation': 'Специализация',
                },
                'help_texts': {
                    'username': 'Это ваш уникальный код!',
                    'email': 'Введите ваш email.',
                    'description': 'Опишите себя, можете добавить контакты.',
                    'specialisation': 'Какая у вас суперсила? Чем вы занимаетесь лучше всего?',
                }
            },
            'default': {
                'labels': {
                    'username': _('Username'),
                    'email': _('Email'),
                    'telegram_id': _('Telegram ID'),
                    'telegram_username': _('Telegram username'),
                    'is_bot': _('Is Bot'),
                    'first_name': _('First name'),
                    'last_name': _('Last name'),
                    'telegram_language': _('Telegram language'),
                    'description': _('Description'),
                    'specialisation': _('Specialisation'),
                },
                'help_texts': {
                    'username': _('This is your unique code!'),
                    'email': _('Enter your email address.'),
                    'description': _('Describe yourself here and you can add contacts.'),
                    'specialisation': _('What is your superpower? What do you do best?'),
                }
            }
        }

        lang = 'ru' if user_language == 'ru' else 'default'
        labels = translations[lang]['labels']
        help_texts = translations[lang]['help_texts']

        readonly_fields = [
            'username',
            'telegram_id',
            'telegram_username',
            'telegram_language',
            'is_bot',
        ]

        for field_name in self.fields:
            field = self.fields[field_name]

            # Устанавливаем переводы
            if field_name in labels:
                field.label = labels[field_name]
            if field_name in help_texts:
                field.help_text = help_texts[field_name]

            # Добавляем общие CSS классы
            field.widget.attrs.update({
                'class': 'w-full p-3 cyber-input rounded',
            })

            # Если поле readonly — делаем его disabled и добавляем атрибут readonly в HTML
            if field_name in readonly_fields:
                field.disabled = True
                field.widget.attrs['readonly'] = 'readonly'


class MapMarkerForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=False,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        widget=forms.NumberInput(attrs={
            'step': '0.0000001',
            'min': '-90.0',
            'max': '90.0',
        }),
        
    )
    longitude = forms.FloatField(
        required=False,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        widget=forms.NumberInput(attrs={
            'step': '0.0000001',
            'min': '-180.0',
            'max': '180.0',
        }),
    )

    class Meta:
        model = MapMarker
        fields = ['latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_language = getattr(self.instance, 'telegram_language', None)

        translations = {
            'ru': {
                'labels': {
                    'user_latitude': 'Широта центра карты',
                    'user_longitude': 'Долгота центра карты'
                },
            },
            'default': {
                'labels': {
                    'user_latitude': _('Latitude of map center'),
                    'user_longitude': _('Longitude of map center'),
                },
            }
        }

        lang = 'ru' if user_language == 'ru' else 'default'
        labels = translations[lang]['labels']

        for field_name in self.fields:
            field = self.fields[field_name]

            # Устанавливаем переводы
            if field_name in labels:
                field.label = labels[field_name]

            # Добавляем общие CSS классы
            field.widget.attrs.update({
                'class': 'w-full p-3 cyber-input rounded',
            })