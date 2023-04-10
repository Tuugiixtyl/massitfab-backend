from django.contrib import admin
from django.urls import path, re_path
from .views import *

app_name = 'mfApi'

urlpatterns = [
    re_path(r'^u/get/(?i)(?P<username>[a-z]+)/$', get_profile, name='get_profile'),
    path('u/update/', update_profile, name='update_profile'),
    
    path('content/create/', create_product, name='upload_content'),
    path('content/update/<int:id>/', update_product, name='update_content'),
    path('content/delete/<int:id>/', delete_product, name='delete_content'),
    path('content/get/<int:id>/', get_product, name='get_content'),
]
