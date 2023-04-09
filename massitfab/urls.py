from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

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

# Serve uploaded files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)