# utils.py

from datetime import datetime, timedelta
from typing import Dict
from rest_framework_simplejwt.tokens import Token

from massitfab import settings


def custom_payload_handler(user: User) -> Dict[str, any]:
    exp = datetime.utcnow() + timedelta(minutes=60)
    user_id = user.id
    username = user.username
    email = user.email
    return {
        'exp': exp,
        'user_id': user_id,
        'username': username,
        'email': email,
        'iss': settings.SITE_URL,
        'iat': datetime.utcnow(),
    }

