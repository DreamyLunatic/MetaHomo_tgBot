from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('users-coordinates/', views.users_coordinates, name='users_coordinates'),
]
