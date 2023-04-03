from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db import connections
from rest_framework_simplejwt.authentication import JWTAuthentication
from massitfab.settings import log_error


class Sandy(BaseBackend):   # CustomBackend
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            with connections['outlaw'].cursor() as cursor:
                cursor.execute("SELECT * FROM fab_user WHERE username=%s", [username])
                row = cursor.fetchone()
                if row:
                    user = UserModel(*row)
                    if user.check_password(password): # type: ignore
                        return user
        except Exception as e:
            log_error('create_product', '{}', str(e))
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            with connections['outlaw'].cursor() as cursor:
                cursor.execute("SELECT * FROM fab_user WHERE id=%s", [user_id])
                row = cursor.fetchone()
                if row:
                    return UserModel(*row)
        except Exception as e:
            log_error('create_product', '{}', str(e))
        return None


class Hideout(JWTAuthentication):   # JWTAuthenticationWithCustomUser
    def get_user(self, payload):
        user_id = payload.get('user_id')
        if user_id:
            return Sandy().get_user(user_id)
        return None
