from django.contrib import admin
from django.urls import path, re_path
from .views import *

app_name = 'mfApi'

urlpatterns = [
    re_path(r'^profile/(?i)(?P<username>[a-z]+)/$', get_profile, name='view_profile'),
    path('content/link/', create_product, name='upload_content'),
    path('items/<int:id>/update/', update_item),
    path('items/<int:id>/delete/', delete_item),
]
