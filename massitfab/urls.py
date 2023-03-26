from django.contrib import admin
from django.urls import path, include

# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

urlpatterns = [
    path('auth/', include('massitfab_auth.urls', namespace='mfAuth')),
    path('api/', include('massitfab_api.urls', namespace='mfApi')),
    path('', include('maesitfab_app.urls', namespace='mfApp')),

    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
