from django.urls import path
from .views import *

urlpatterns = [
    path('run_module', run_module, name='run_module'),
    path('notify_event', notify_event, name='notify_event'),
    path('send_message/<int:param1>/<str:param2>', send_message, name='send_message'),
]
