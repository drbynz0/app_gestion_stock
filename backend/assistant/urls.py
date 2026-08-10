from django.urls import path # type: ignore
from .views import ask_ai

urlpatterns = [
    path('ask-ai/', ask_ai, name='ask_ai'),
]