from django.conf.urls import include
from django.urls import path
from .views import *

urlpatterns = [
    path('run_module', run_module, name='run_module'),
    path('send_message/<int:param1>/<str:param2>', send_message, name='send_message'),
    path('<str:param1>/<str:param2>', process_api, name='webhook'),
    # path('<int:param1>/<int:param2>/', process_api, name='webhook'),


]
