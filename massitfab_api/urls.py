from django.contrib import admin
from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'mfApi'

urlpatterns = [
    path('items/', get_items),
    path('items/create/', create_item),
    path('items/<int:id>/update/', update_item),
    path('items/<int:id>/delete/', delete_item),
    path('register/', RegisterView.as_view(), name="sign_up"),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
