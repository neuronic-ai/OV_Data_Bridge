from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['35.193.25.247', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'ovdatabridge',
        'USER': 'root',
        'PASSWORD': '',
        'PORT': '3306',
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

ASGI_APPLICATION = 'config.asgi.application'
