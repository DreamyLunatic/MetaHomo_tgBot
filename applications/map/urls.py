from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path("markers/", views.MarkerList.as_view(), name='marker_list'),
    path("markers/create/", views.MarkerCreate.as_view(), name='marker_create'),
    path("markers/<int:pk>/update/", views.MarkerUpdate.as_view(), name='marker_update'),
    path("markers/<int:pk>/delete/", views.MarkerDelete.as_view(), name='marker_delete'),
]
