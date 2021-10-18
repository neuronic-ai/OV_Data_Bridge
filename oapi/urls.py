from django.urls import path
from .views import *

urlpatterns = [
    path('<str:param1>/bridge', BridgeApi.as_view(), name='bridge'),
]
