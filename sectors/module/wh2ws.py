import time
from datetime import datetime
import json

from . import common, log

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    WebHook to WebSocket Data Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.log = log.BridgeLog(bridge_info)
        self.cache = self.log.get_last_log()
        self.ws_clients = []

    def open(self):
        self.connection_status = True
        self.connection_text = 'WH:Open - Ready'
        self.add_cache(self.connection_text)

    def close_log(self):
        self.log.close()

    def close(self):
        self.log.close()
        self.connection_status = False
        self.connection_text = f'WH:Closed'
        self.add_cache(self.connection_text)

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def add_ws_client(self, ws_id):
        self.ws_clients.append(ws_id)

    def remove_ws_client(self, ws_id):
        self.ws_clients.remove(ws_id)

    def send_message(self, message):
        self.add_cache(f'WH:Recv - {message}')
        try:
            replaceable, content = common.get_formatted_content(message, self.bridge_info)
            if replaceable:
                self.add_cache(f'WS:Send - {content}')

                for ws_id in self.ws_clients:
                    common.send_ws_message(ws_id, content)

                bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
                bridge.api_calls += 1
                bridge.save()
            else:
                self.add_cache(f'WS:Send - Ignored!')
        except Exception as e:
            self.add_cache(f'WS:Send - Exception - {e}')

    def add_cache(self, data):
        self.trace(data)

        if len(self.cache) > admin_config.LOCAL_CACHE_LIMIT:
            self.cache.pop(0)

        cache_data = {
            'date': datetime.now().strftime('%m/%d/%Y, %H:%M:%S'),
            'data': data
        }
        self.cache.append(cache_data)

        self.log.write_log(json.dumps(cache_data))

    def get_cache(self):
        return self.cache

    def trace(self, trace_log):
        if admin_config.TRACE_MODE:
            print(f"{datetime.now()}: {self.bridge_info['name']}_{self.bridge_info['user_id']}: {trace_log}")
