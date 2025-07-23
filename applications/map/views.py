from turtle import color
import telegram
from django.contrib.auth import get_user_model
from django.views import generic
from rest_framework import generics, status
from rest_framework.permissions import (AllowAny, BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.serializers import TokenVerifySerializer
from django.http import JsonResponse
from applications.account.models import MapMarker

User = get_user_model()
bot = telegram.Bot('...')


class IndexView(generic.TemplateView):
    template_name = 'map/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_latitude_center = '48.72672'
        default_longitude_center = '2.37854'

        context['user_latitude'] = default_latitude_center
        context['user_longitude'] = default_longitude_center

        return context
    
# Функция API для отдачи координат пользователей
def users_coordinates(request):
    markers = MapMarker.objects.all()

    user_markers_dict = {}
    for marker in markers:
        if marker.user and marker.latitude and marker.longitude:
            user_markers_dict[marker.user.id] = {
                'username': marker.user.username,
                'full_name': marker.user.get_full_name(),
                'telegram_username': marker.user.telegram_username,
                'specialisation': marker.user.specialisation,
                'description': marker.user.description,
                'lat': marker.latitude,
                'lng': marker.longitude,
                'color': "#2BFF00",  # Default color for markers
            }

    return JsonResponse(user_markers_dict, safe=False)