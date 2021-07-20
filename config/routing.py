from django.urls import path
from wsocket.consumer import *

websocket_urlpatterns = [
    path('websocket/<str:param1>/<str:param2>', BridgeConsumer.as_asgi(), name='bridge-consumer')
]