from django.conf.urls import include
from django.urls import path
from .views import *

urlpatterns = [
    path('<str:param1>/<str:param2>', process_webhook, name='webhook'),
]
