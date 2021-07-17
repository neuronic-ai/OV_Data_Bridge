from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import time
import json

from sectors.common import admin_config
from sectors.module import bridge


# Create your views here.
def run_module(request):
    if admin_config.BRIDGE_HANDLE is None:
        admin_config.BRIDGE_HANDLE = bridge.BridgeQueue()
        admin_config.BRIDGE_HANDLE.fetch_all_bridges()
        admin_config.BRIDGE_HANDLE.start_all()

        return JsonResponse({
            'status_code': 200,
            'text': 'Module Started'
        })
    else:
        return JsonResponse({
            'status_code': 200,
            'text': 'Already Running'
        })


# Test function
def send_message(request, param1, param2):
    admin_config.BRIDGE_HANDLE.send_message(param1, param2)

    return JsonResponse({
        'status_code': 200,
        'text': 'Sent'
    })
