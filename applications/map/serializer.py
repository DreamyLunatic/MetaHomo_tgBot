from rest_framework import serializers
from django.contrib.auth import get_user_model

from applications.map import models

User = get_user_model()


class MarkerGetSerializer(serializers.ModelSerializer):
    telegram_id = serializers.IntegerField(required=False, min_value=0, source='user.telegram_id')
    telegram_username = serializers.CharField(required=False, allow_blank=True, source='user.telegram_username')
    is_owner = serializers.BooleanField(required=False)

    class Meta:
        model = models.Marker
        fields = [
            'id',
            'latitude',
            'longitude',
            'time',
            'message',
            'photo',
            'is_owner',
            'telegram_id',
            'telegram_username',
        ]


class MarkerPostSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Marker
        fields = [
            'latitude',
            'longitude',
            'time',
            'message',
            'photo',
            'user',
        ]


class MarkerPutSerializer(serializers.ModelSerializer):
    is_delete_photo = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.Marker
        fields = [
            'latitude',
            'longitude',
            'time',
            'message',
            'photo',
            'is_delete_photo',
        ]


class MarkerDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Marker
        fields = [
            'id'
        ]
