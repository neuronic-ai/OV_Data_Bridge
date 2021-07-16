from django.urls import path
from wsocket.consumer import *

websocket_urlpatterns = [
    path(
        'websocket/jong/<str:param1>/<str:param2>',
        JongConsumer.as_asgi(),
        name='jong-consumer',
    )
]