import time
from datetime import datetime
import json

from . import common, log

from sectors.common import admin_config

from db.models import (
    TBLBridge,
)


class Bridge:
    """
    WebSocket to WebHook Data Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.cache = []
        self.log = log.BridgeLog(bridge_info)

    def open(self):
        self.connection_status = True
        self.connection_text = 'WH:Open - Ready'
        self.add_cache(self.connection_text)

    def close(self):
        self.connection_status = False
        self.connection_text = f'WH:Closed'
        self.add_cache(self.connection_text)

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def send_message(self, message):
        self.add_cache(f'WH:Recv - {message}')
        try:
            content = common.get_formatted_content(message, self.bridge_info)

            self.add_cache(f'WS:Send - {content}')

            common.send_ws_message(f"{admin_config.BRIDGE_CONSUMER_PREFIX}_{self.bridge_info['id']}", content)

            bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
            bridge.api_calls += 1
            bridge.save()
        except Exception as e:
            self.add_cache(f'WS:Send - Exception - {e}')

    def add_cache(self, data):
        self.trace(data)

        if len(self.cache) > admin_config.LOCAL_CACHE_LIMIT:
            self.cache.pop(0)

        cache_data = {
            'date': datetime.now(),
            'data': data
        }
        self.cache.append(cache_data)

        cache_data['date'] = cache_data['date'].strftime("%m/%d/%Y, %H:%M:%S")
        self.log.write_log(json.dumps(cache_data))

    def get_cache(self):
        return self.cache

    def trace(self, trace_log):
        if admin_config.TRACE_MODE:
            print(f"{datetime.now()}: {self.bridge_info['name']}_{self.bridge_info['user_id']}: {trace_log}")
