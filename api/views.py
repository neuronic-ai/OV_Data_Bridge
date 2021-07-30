from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from django.core.cache import cache
import time

from sectors.common import admin_config, error
from sectors.module import bridge

from db.models import (
    TBLBridge
)


# Create your views here.
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


# Test function
def send_message(request, param1, param2):
    admin_config.BRIDGE_HANDLE.send_message(param1, param2)

    return JsonResponse({
        'status_code': status.HTTP_200_OK,
        'text': 'Sent'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def process_api(request, param1, param2):
    try:
        bridge = TBLBridge.objects.get(dst_address__icontains=request.path, is_active=True)
    except:
        time.sleep(admin_config.DELAY_FOR_BAD_REQUEST)
        return JsonResponse({
            'status_code': status.HTTP_400_BAD_REQUEST,
            'text': error.INVALID_URL
        }, status=status.HTTP_400_BAD_REQUEST)

    redis_cache_id = f'{admin_config.BRIDGE_REDIS_CACHE_PREFIX}_{bridge.id}'
    print(redis_cache_id)
    if redis_cache_id in cache:
        print('exist')
        data = cache.get(redis_cache_id)
    else:
        data = []

    bridge.api_calls += 1
    bridge.save()

    return JsonResponse({
        'frequency (s)': bridge.frequency,
        'content': data
    }, status=status.HTTP_200_OK)
