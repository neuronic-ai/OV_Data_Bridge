from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from django.core.cache import cache
from datetime import datetime, timedelta
import time
import json

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

    rate_limit_id = f'{admin_config.RATE_LIMIT_REDIS_CACHE_PREFIX}_{bridge.id}'
    if rate_limit_id in cache:
        data = cache.get(rate_limit_id)
        for d in data:
            if d < datetime.now() - timedelta(minutes=1):
                data.remove(d)

        rate_limit_per_url = json.loads(bridge.user.permission)['rate_limit_per_url']

        if len(data) < rate_limit_per_url:
            data.append(datetime.now())
            cache.set(rate_limit_id, data, timeout=60)
        else:
            return JsonResponse({
                'status_code': status.HTTP_406_NOT_ACCEPTABLE,
                'text': f'{error.RATE_LIMIT_PER_URL_EXCEED} - {rate_limit_per_url}'
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        cache.set(rate_limit_id, [datetime.now()], timeout=60)

    redis_cache_id = f'{admin_config.BRIDGE_REDIS_CACHE_PREFIX}_{bridge.id}'
    if redis_cache_id in cache:
        data = cache.get(redis_cache_id)
    else:
        data = []

    bridge.api_calls += 1
    bridge.save()

    return JsonResponse({
        'frequency (s)': bridge.frequency,
        'content': data
    }, status=status.HTTP_200_OK)
