from django.urls import path # type: ignore
from .views import request_reset_code, verify_code, reset_password, change_password

urlpatterns = [
    path('password_reset/', request_reset_code, name='password_reset'),
    path('password_reset/verify/', verify_code, name='verify_code'),
    path('password_reset/save/', reset_password, name='reset_password'),
    path('password_change/', change_password, name='change_password'),
]