from django.contrib import admin
from django.urls import path, re_path
from .views import *

app_name = 'mfApi'

urlpatterns = [
    re_path(r'^profile/(?i)(?P<username>[a-z]+)/$', get_profile, name='get_profile'),
    path('content/link/', create_product, name='upload_content'),
    path('content/<int:id>/update/', edit_product, name='update_product'),
    path('items/<int:id>/delete/', delete_product),
    path('product/<int:id>/', get_products, name='get_products'),
    # path('profile/<int:id>/', update_profile, name='update_profile'),
]
