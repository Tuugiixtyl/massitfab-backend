from pathlib import Path
from datetime import timedelta
import environ
import psycopg2 as ps
import hashlib

# ==============================================================================
# TYPE SAFETY START POINT
# ==============================================================================

class AuthException(Exception):
    pass

ROOT_URLCONF = 'massitfab.urls'

DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / 'massitfab/etc/.env')

SECRET_KEY = env('SECRET_KEY')

WSGI_APPLICATION = 'massitfab.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'public']

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
encoding = "utf-8"
USE_TZ = True

params = {
    'database': env('DATABASE_NAME'),
    'user': env('DATABASE_USER'),
    'password': env('DATABASE_PASS'),
    'host': env('DATABASE_HOST'),
    'port': env('DATABASE_PORT'),
}

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# CSRF_COOKIE_SECURE = True
# CSRF_COOKIE_HTTPONLY = True
# SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True

# SESSION_COOKIE_SECURE = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    ]

INSTALLED_APPS = [
    'maesitfab_app',
    'massitfab_auth',
    'massitfab_api',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'src'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'outlaw': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': params['database'],
        'USER': params['user'],
        'PASSWORD': params['password'],
        'HOST': params['host'],
        'PORT': params['port'],
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==============================================================================
# THIRD-PARTY APPS SETTINGS
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'massitfab_auth.auth_backend.Hideout',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOWED_ORIGINS = [
#     "http://127.0.0.1:4000",
#     "http://localhost:4000"
# ]

# ==============================================================================
# MASSITFAB ESSENTIALS
# ==============================================================================

def connectDB():
    con = ps.connect(**params)
    return con

def disconnectDB(con):
    if(con):
        con.close()

def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def hashPassword(user_pass):
    password = user_pass
    hash_object = hashlib.sha256(password.encode())
    hashed_password = hash_object.hexdigest()
    return hashed_password

def verifyPassword(hashed_password, stored_password):
    if hashed_password == stored_password:
        return True
    return False