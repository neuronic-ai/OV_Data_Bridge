from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['bridge.vantagecrypto.com']
# ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'HOST': 'localhost',
#         'NAME': 'ovdatabridge',
#         'USER': 'root',
#         'PASSWORD': '',
#         'PORT': '3306',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'ovdatabridge',
        'USER': 'ovdatabridge1',
        'PASSWORD': 'z63p7GU3UbXBtyWvLqEZcL79vswwZQMW',
        'PORT': '3307',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('35.193.25.247', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://35.193.25.247:6379/',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

ASGI_APPLICATION = 'config.asgi.application'
