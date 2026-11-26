from django.urls import path
from .views import WatchedListView, WatchedToggleView

urlpatterns = [
    path('watched/', WatchedListView.as_view(), name='watched-list'),
    path('watched/toggle/', WatchedToggleView.as_view(), name='watched-toggle'),
]
