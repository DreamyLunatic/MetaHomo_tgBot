from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.db.models import Min

from . import forms
from .models import User, MapMarker
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
import random
import json

def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


@csrf_protect
def user_settings_page(request):
    user = None
    access_token = ''
    refresh_token = ''

    access = request.GET.get('access') or request.COOKIES.get('access_token', '')
    refresh = request.GET.get('refresh') or request.COOKIES.get('refresh_token', '')

    # Проверяем access
    if access:
        try:
            token_obj = AccessToken(access)
            user_id = token_obj.get("user_id")
            user = User.objects.filter(id=user_id, is_active=True).first()
        except Exception:
            access = ''

    # Если access не сработал — пробуем refresh
    if not user and refresh:
        try:
            refresh_obj = RefreshToken(refresh)
            refresh_token = str(refresh_obj)
            access_token = str(refresh_obj.access_token)
            user = User.objects.filter(id=refresh_obj.get("user_id"), is_active=True).first()
        except Exception:
            refresh = ''

    # Если пользователь есть, но refresh_token ещё не выдан — выдаём
    if user and not refresh_token:
        refresh_obj = RefreshToken.for_user(user)
        refresh_token = str(refresh_obj)
        access_token = str(refresh_obj.access_token)

    if not user:
        return redirect('https://t.me/MetaHomoBot?start=login')

    # Получаем текущую метку (если есть)
    marker = MapMarker.objects.filter(user=user).first() if user else None

    if request.method == 'POST':
        user_form = forms.UserForm(request.POST, instance=user) if user else forms.UserForm(request.POST)
        marker_form = forms.MapMarkerForm(request.POST)

        if user_form.is_valid() and marker_form.is_valid():
            user_form.save()

            lat = marker_form.cleaned_data.get('latitude')
            lon = marker_form.cleaned_data.get('longitude')

            if lat is not None and lon is not None:
                try:
                    latitude = float(lat)
                    longitude = float(lon)

                    # Удаляем старую метку (меток не должно/не может быть больше одной)
                    MapMarker.objects.filter(user=user).delete()

                    # Создаём новую
                    MapMarker.objects.create(user=user, latitude=latitude, longitude=longitude)
                    messages.success(request, _("Marker updated successfully."))
                except ValueError:
                    messages.error(request, _("Invalid coordinates."))

            messages.success(request, _("Settings successfully updated!"))
            return redirect('account:user_settings_page')
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        user_form = forms.UserForm(instance=user) if user else forms.UserForm()
        marker_initial = {'latitude': marker.latitude, 'longitude': marker.longitude} if marker else {}
        marker_form = forms.MapMarkerForm(initial=marker_initial)

    lang = user.telegram_language if user else 'en'
    if lang == 'ru':
        sections = {
            'header_title': 'РЕГИСТР ТРАНСГУМАНИСТОВ',
            'header_description': 'Присоединяйтесь к эволюции. Поделитесь своими данными для развития технологий улучшения человека.\nВаш вклад прокладывает путь к следующему этапу развития человечества.',
            'user_data': 'Данные пользователя',
            'profile_info': 'Профиль',
            'map_settings': 'Сеть трансгуманистов',
            'description': 'О себе',
            'save_changes': 'Сохранить изменения',
        }
    else:
        sections = {
            'header_title': 'TRANSHUMANIST REGISTRY',
            'header_description': 'Join the evolution. Volunteer your data to advance human enhancement technologies.\nYour contribution paves the way for the next stage of human development.',
            'user_data': 'User Data',
            'profile_info': 'Profile',
            'map_settings': 'Transhumanist network',
            'description': 'About Yourself',
            'save_changes': 'Save Changes',
        }

    users_with_first_marker_time = (
        User.objects
        .annotate(first_marker_time=Min('map_markers__created_at'))
        .filter(first_marker_time__isnull=False)
        .order_by('-first_marker_time')[:3]
    )

    user_markers_dict = {}

    for user in users_with_first_marker_time:
        first_marker = user.map_markers.order_by('created_at').first()
        if first_marker and first_marker.latitude and first_marker.longitude:
            user_markers_dict[user.id] = {
                'username': user.username,
                'full_name': user.get_full_name(),
                'specialisation': user.specialisation,
                'description': user.description,
                'lat': first_marker.latitude,
                'lng': first_marker.longitude,
                'color': get_random_color(),
            }

    user_markers_json = json.dumps(list(user_markers_dict.values()))


    response = render(request, 'account/new_settings.html', {
        'user': user,
        'user_form': user_form,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'marker_form': marker_form,
        'sections': sections,
        'first_marker_users': users_with_first_marker_time,
        'user_markers_json': user_markers_json,
        'user_markers_dict': user_markers_dict,
    })

    if request.GET.get('access') and request.GET.get('refresh'):
        response.set_cookie('access_token', access, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('refresh_token', refresh, httponly=True, secure=True, samesite='Lax')

    return response

