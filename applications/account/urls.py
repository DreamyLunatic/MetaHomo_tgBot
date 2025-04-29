from django.urls import path

from . import views


urlpatterns = [
    path("user/settings/", views.user_settings_page, name="user_settings_page"),
]
