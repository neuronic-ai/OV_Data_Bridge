from rest_framework.views import APIView
from rest_framework import status
from django.http import JsonResponse
import json

from sectors.common import error
from sectors.common.bridge import common as bridge_common

from db.models import (
    TBLApiKey,
    TBLBridge,
)


def get_user(request, unique_id):
    if TBLApiKey.objects.filter(unique_id=unique_id, api_key=request.headers.get('api-key')).exists():
        api_key = TBLApiKey.objects.get(unique_id=unique_id, api_key=request.headers.get('api-key'))
        return api_key.user

    return None


def api_decorator():
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            user = get_user(request, kwargs['param1'])
            if user is None:
                text = error.INVALID_UNIQUE_ID_API_KEY
                status_code = status.HTTP_401_UNAUTHORIZED
                return JsonResponse({
                    'text': text
                }, status=status_code)

            kwargs['user'] = user
            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def parse_bridge_params(request):
    payload = request.data

    bridge_id = 0
    if request.method == 'POST':
        if 'type' not in payload:
            return {
                'status_code': status.HTTP_400_BAD_REQUEST,
                'text': '"type" field required for the request.'
            }
        if 'name' not in payload:
            return {
                'status_code': status.HTTP_400_BAD_REQUEST,
                'text': '"name" field required for the request.'
            }
    elif request.method == 'PUT':
        if 'id' not in payload:
            return {
                'status_code': status.HTTP_400_BAD_REQUEST,
                'text': '"id" field required for the request.'
            }

        try:
            bridge_id = int(payload['id'])
        except:
            bridge_id = 0

        if not bridge_id or not TBLBridge.objects.filter(id=bridge_id).exists():
            return {
                'status_code': status.HTTP_400_BAD_REQUEST,
                'text': error.UNKNOWN_BRIDGE_ID
            }

        if 'type' not in payload:
            bridge_type = TBLBridge.objects.get(id=bridge_id).type
            payload['type'] = bridge_common.get_bridge_by_type(bridge_type)['abbreviation']
    else:
        pass

    b = bridge_common.get_bridge_by_abb(payload['type'])
    if b is None:
        return {
            'status_code': status.HTTP_400_BAD_REQUEST,
            'text': error.UNKNOWN_BRIDGE_TYPE
        }

    params = {
        'id': bridge_id,
        'type': b['type'],
    }

    if 'name' in payload:
        params['name'] = payload['name']

    if b['src'] in payload:
        params['src_address'] = payload[b['src']]

    if b['dst'] in payload:
        params['dst_address'] = payload[b['dst']]

    if 'format_search' in payload and 'format_re_format' in payload and 'format_any' in payload:
        params['format'] = json.dumps({
            'search_word': payload['format_search'],
            'replace_word': payload['format_re_format'],
            'any': True if payload['format_any'].lower() == 'yes' else False
        })

    if 'frequency' in payload:
        params['frequency'] = payload['frequency']

    if 'flush' in payload:
        params['flash'] = payload['flush']

    if 'file_format' in payload:
        params['file_format'] = payload['file_format']

    return {
        'status_code': status.HTTP_200_OK,
        'params': params
    }


class BridgeApi(APIView):

    @api_decorator()
    def post(self, request, *args, **kwargs):
        bridge_info = {}
        resp_data = parse_bridge_params(request)
        if resp_data['status_code'] < 300:
            resp_data, bridge = bridge_common.save_bridge(request, resp_data['params'], kwargs['user'])
            if resp_data['status_code'] < 300:
                bridge_info['id'] = bridge.id

        if not bridge_info:
            bridge_info = resp_data['text']

        return JsonResponse(bridge_info, status=resp_data['status_code'])

    @api_decorator()
    def get(self, request, *args, **kwargs):
        payload = request.data
        status_code = status.HTTP_200_OK
        if 'id' not in payload:
            resp_data = '"id" field required for the request.'
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            resp_data = []
            if payload['id'] == 'all':
                bridges_obj = TBLBridge.objects.filter(user_id=kwargs['user_id'])
            else:
                try:
                    bridge_id = int(payload['id'])
                    bridges_obj = TBLBridge.objects.filter(id=bridge_id)
                except:
                    bridges_obj = []
                    status_code = status.HTTP_400_BAD_REQUEST

            for bridge in bridges_obj:
                b = bridge_common.get_bridge_by_type(bridge.type)
                b_info = {
                    'id': bridge.id,
                    'name': bridge.name,
                    'type': b['abbreviation'],
                    b['src']: bridge.src_address,
                    b['dst']: bridge.dst_address
                }

                if bridge.format:
                    bridge_format = json.loads(bridge.format)
                    b_info['format_search'] = bridge_format['search_word']
                    b_info['format_re_format'] = bridge_format['replace_word']
                    b_info['format_any'] = 'Yes' if bridge_format['any'] else 'No'

                if bridge.frequency:
                    b_info['frequency'] = bridge.frequency

                if bridge.flush:
                    b_info['flush'] = bridge.flush

                if bridge.file_format:
                    b_info['file_format'] = bridge.file_format

                resp_data.append(b_info)

        return JsonResponse(resp_data, status=status_code, safe=False)

    @api_decorator()
    def put(self, request, *args, **kwargs):
        resp_data = parse_bridge_params(request)
        if resp_data['status_code'] < 300:
            resp_data, _ = bridge_common.save_bridge(request, resp_data['params'], kwargs['user'])
            if resp_data['status_code'] < 300:
                return JsonResponse('', status=status.HTTP_202_ACCEPTED, safe=False)

        return JsonResponse(resp_data['text'], status=resp_data['status_code'])

    @api_decorator()
    def delete(self, request, *args, **kwargs):
        payload = request.data
        resp_data = ''
        status_code = status.HTTP_202_ACCEPTED
        if 'id' not in payload:
            resp_data = '"id" field required for the request.'
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            if payload['id'] == 'all':
                TBLBridge.objects.filter(user_id=kwargs['user_id']).delete()
            else:
                try:
                    bridge_id = int(payload['id'])
                    TBLBridge.objects.filter(id=bridge_id).delete()
                except:
                    status_code = status.HTTP_406_NOT_ACCEPTABLE

        return JsonResponse(resp_data, status=status_code, safe=False)
