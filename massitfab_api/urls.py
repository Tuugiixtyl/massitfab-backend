from django.contrib import admin
from django.urls import path
from massitfab_api.views import *

app_name = 'mfApi'

urlpatterns = [
    path('admin/', admin.site.urls),
]