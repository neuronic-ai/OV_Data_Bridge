import time
import _thread as thread

from . import ws2wh, wh2ws, ws2api, api2ws

from sectors.common import error

from db.models import (
    TBLBridge
)


class BridgeQueue:
    """
    BridgeQueue to manage all Data Bridges
    """

    def __init__(self):
        self.bridges_info = []
        self.bridges_obj = []

    def fetch_all_bridges(self):
        self.bridges_info = list(TBLBridge.objects.filter(is_active=True).values())

    def open_bridge(self, bridge_info):
        if bridge_info['type'] == 1:  # ws2wh
            b_obj = ws2wh.Bridge(bridge_info)
            b_obj.open()
        elif bridge_info['type'] == 2:  # wh2ws
            b_obj = wh2ws.Bridge(bridge_info)
            b_obj.open()
        elif bridge_info['type'] == 3:  # ws2api
            b_obj = ws2api.Bridge(bridge_info)
            b_obj.open()
        elif bridge_info['type'] == 4:  # api2ws
            b_obj = api2ws.Bridge(bridge_info)
            b_obj.open()
        else:
            return False, error.UNKNOWN_BRIDGE_TYPE

        self.bridges_obj.append({
            'id': bridge_info['id'],
            'obj': b_obj,
            'status': False
        })

        return True, error.SUCCESS

    def start_all(self):
        for bridge_info in self.bridges_info:
            self.open_bridge(bridge_info)

        thread.start_new_thread(self.update_connection_status, ())

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
            bridge_info = list(TBLBridge.objects.filter(id=bridge_id).values())[0]
            return self.open_bridge(bridge_info)

        return True, error.SUCCESS

    def restart_bridge_by_id(self, bridge_id):
        self.remove_bridge_by_id(bridge_id)
        bridge_info = list(TBLBridge.objects.filter(id=bridge_id).values())[0]
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
                if b_obj['status']:
                    b_obj['obj'].close()
                b_obj['obj'].close_log()
                self.bridges_obj.remove(b_obj)
                return True, error.SUCCESS

        return False, error.UNKNOWN_BRIDGE_ID

    def get_bridge_cache(self, bridge_id):
        cache = []
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id:
                cache = b_obj['obj'].get_cache()
                break

        return cache

    def send_message(self, bridge_id, message):
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id and b_obj['status']:
                b_obj['obj'].send_message(message)
                return True

        return False

    def add_ws_client(self, bridge_id, ws_id):
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id and b_obj['status']:
                b_obj['obj'].add_ws_client(ws_id)
                break

    def remove_ws_client(self, bridge_id, ws_id):
        for b_obj in self.bridges_obj:
            if b_obj['id'] == bridge_id and b_obj['status']:
                b_obj['obj'].remove_ws_client(ws_id)
                break
