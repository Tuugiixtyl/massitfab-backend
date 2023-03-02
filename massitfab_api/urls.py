from django.contrib import admin
from django.urls import path
from .views import *

app_name = 'mfApi'

urlpatterns = [
    path('items/', get_items),
    path('items/create/', create_item),
    path('items/<int:id>/update/', update_item),
    path('items/<int:id>/delete/', delete_item),
]
