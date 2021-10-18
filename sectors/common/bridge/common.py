import json
from rest_framework import status

from sectors.common import admin_config, error
from sectors.module import common, billing

from db.models import (
    TBLBridge,
)


def save_bridge(request, params, user):
    if int(params['id']) == 0:  # new bridge
        bridge = TBLBridge()
    else:
        bridge = TBLBridge.objects.get(id=int(params['id']))
        if bridge.user_id != user.id:
            return {
                'status_code': status.HTTP_400_BAD_REQUEST,
                'text': error.PERMISSION_NOT_ALLOWED
            }, None

    bridge_type = int(params['type'])

    if bridge_type in [5, 6, 7]:
        resp_data, status_code = common.check_validity_remote_file(request, params['src_address'])
        if status_code >= 300:
            return {
                'status_code': status_code,
                'text': resp_data
            }, None

    bridge.user_id = user.id
    if 'name' in params:
        bridge.name = params['name']
    bridge.type = bridge_type
    if 'src_address' in params:
        bridge.src_address = params['src_address']
    if 'dst_address' in params:
        bridge.dst_address = params['dst_address']
    if 'format' in params:
        bridge.format = params['format']
    if 'frequency' in params:
        bridge.frequency = int(params['frequency'])
    if 'flush' in params:
        bridge.flush = int(params['flush'])
    if 'file_format' in params:
        bridge.file_format = params['file_format']

    bridge_qty = TBLBridge.objects.filter(user_id=user.id, is_active=True).count()
    if int(params['id']) == 0:
        bridge_qty += 1

    max_active_bridges = json.loads(user.permission)['max_active_bridges']
    if max_active_bridges < bridge_qty:
        bridge.is_active = False

    bridge.save()

    if bridge.is_active:
        admin_config.BRIDGE_HANDLE.restart_bridge_by_id(bridge.id)

    billing.check_bridge_out_of_funds(user.id)

    return {
        'status_code': status.HTTP_201_CREATED,
        'text': error.SUCCESS
    }, bridge


def get_bridge_by_type(b_type):
    for b in admin_config.BRIDGE:
        if b['type'] == b_type:
            return b

    return None


def get_bridge_by_abb(b_abb):
    for b in admin_config.BRIDGE:
        if b['abbreviation'] == b_abb:
            return b

    return None


def get_frequency_by_type(f_type):
    for f in admin_config.FREQUENCY:
        if f['type'] == f_type:
            return f

    return None
