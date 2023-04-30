from django.urls import path
from .views import *

app_name = 'mfAuth'

urlpatterns = [
    path('register', RegisterUserApi.as_view(), name='register'),
    path('login', LoginUserApi.as_view(), name='login'),
]

