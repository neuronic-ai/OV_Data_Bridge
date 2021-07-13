from django.conf.urls import include
from django.urls import path
from .views import *

urlpatterns = [
    path('<int:param1>/<int:param2>/', process_webhook, name='webhook'),
]