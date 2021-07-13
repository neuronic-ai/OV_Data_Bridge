import time

from . import ws2wh
from sectors.common import error

from db.models import (
    TBLBridge,
)


class BridgeQueue:
    """
    BridgeQueue to manage all Data Bridges
    """

    def __init__(self):
        self.bridges_info = []
        self.bridges_obj = []

    def fetch_all_bridges(self):
        self.bridges_info = TBLBridge.objects.get(is_active=True)

    def open_bridge(self, bridge_info):
        if bridge_info.type == 1:  # ws2wh
            b_obj = ws2wh.Bridge(bridge_info)
            b_obj.open()
        elif bridge_info.type == 2:  # wh2ws
            b_obj = None
        elif bridge_info.type == 3:  # ws2api
            b_obj = None
        elif bridge_info.type == 4:  # api2ws
            b_obj = None
        else:
            return False, error.UNKNOWN_BRIDGE_TYPE

        self.bridges_obj.append({
            'id': bridge_info.id,
            'obj': b_obj,
            'status': True
        })

        return True, error.SUCCESS

    def start_all(self):
        for bridge_info in self.bridges_info:
            self.open_bridge(bridge_info)

        self.update_connection_status()

    def update_connection_status(self):
        while True:
            for b_obj in self.bridges_obj:
                b_obj['status'] = b_obj['obj'].is_connected()

            time.sleep(60)

    def start_bridge_by_id(self, bridge_id):
        new_bridge = True
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id:
                b_obj['obj'].open()
                new_bridge = False
                break

        if new_bridge:
            bridge_info = TBLBridge.objects.get(id=bridge_id)
            return self.open_bridge(bridge_info)

        return True, error.SUCCESS

    def restart_bridge_by_id(self, bridge_id):
        res, text = self.remove_bridge_by_id(bridge_id)
        if not res:
            return res, text

        bridge_info = TBLBridge.objects.get(id=bridge_id)
        return self.open_bridge(bridge_info)

    def stop_bridge_by_id(self, bridge_id):
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id:
                b_obj['obj'].close()
                b_obj['status'] = False
                return True, error.SUCCESS

        return False, error.UNKNOWN_BRIDGE_ID

    def remove_bridge_by_id(self, bridge_id):
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id:
                b_obj['obj'].close()
                self.bridges_obj.remove(b_obj)
                return True, error.SUCCESS

        return False, error.UNKNOWN_BRIDGE_ID
