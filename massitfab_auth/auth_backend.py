from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db import connections
from rest_framework_simplejwt.authentication import JWTAuthentication


class Sandy(BaseBackend):   # CustomBackend
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        with connections['outlaw'].cursor() as cursor:
            cursor.execute("SELECT * FROM creator WHERE username=%s", [username])
            row = cursor.fetchone()
            if row:
                user = UserModel(*row)
                if user.check_password(password):
                    return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        with connections['outlaw'].cursor() as cursor:
            cursor.execute("SELECT * FROM creator WHERE id=%s", [user_id])
            row = cursor.fetchone()
            if row:
                return UserModel(*row)
        return None


class Hideout(JWTAuthentication):   # JWTAuthenticationWithCustomUser
    def get_user(self, payload):
        user_id = payload.get('user_id')
        if user_id:
            return Sandy().get_user(user_id)
        return None
