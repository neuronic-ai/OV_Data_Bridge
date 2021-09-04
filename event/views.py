from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
import json

from sectors.common import admin_config, error
from sectors.module import bridge


def run_module(request):
    if admin_config.BRIDGE_HANDLE is None:
        admin_config.BRIDGE_HANDLE = bridge.BridgeQueue()
        admin_config.BRIDGE_HANDLE.fetch_all_bridges()
        admin_config.BRIDGE_HANDLE.start_all()

        return JsonResponse({
            'status_code': status.HTTP_200_OK,
            'text': 'Module Started'
        }, status=status.HTTP_200_OK)
    else:
        return JsonResponse({
            'status_code': status.HTTP_201_CREATED,
            'text': 'Already Running'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def notify_event(request):
    if isinstance(request.body, bytes):
        message = request.body.decode()
    elif isinstance(request.body, str):
        message = request.body
    else:
        message = str(request.body)

    message = json.loads(message)

    admin_config.BRIDGE_HANDLE.notify_event(message)

    return JsonResponse({
        'status_code': status.HTTP_200_OK,
        'text': error.SUCCESS
    }, status=status.HTTP_200_OK)


# Test function
def send_message(request, param1, param2):
    res = admin_config.BRIDGE_HANDLE.send_message(param1, param2)

    if res:
        return JsonResponse({
            'status_code': status.HTTP_200_OK,
            'text': 'Sent'
        }, status=status.HTTP_200_OK)
    else:
        return JsonResponse({
            'status_code': status.HTTP_406_NOT_ACCEPTABLE,
            'text': 'No Bridge or Inactive'
        }, status=status.HTTP_406_NOT_ACCEPTABLE)
