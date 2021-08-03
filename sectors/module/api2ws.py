from django.core.cache import cache
import _thread as thread
import time
from datetime import datetime
import requests
import json

from . import common, log

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    API to WebSocket Data Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.log = log.BridgeLog(bridge_info)
        self.cache = self.log.get_last_log()
        self.ws_clients = []

        self.REDIS_CACHE_ID = f"{admin_config.BRIDGE_REDIS_CACHE_PREFIX}_{self.bridge_info['id']}"
        self.REDIS_CACHE_TTL = self.bridge_info['frequency']

    def run_api(self):
        count = 0
        while True:
            if not self.connection_status:
                break

            if count == 0 or count >= self.REDIS_CACHE_TTL:
                try:
                    self.add_cache(f"API:Call - {self.bridge_info['src_address']}")
                    res = requests.get(self.bridge_info['src_address'], verify=False)
                    try:
                        cache.set(self.REDIS_CACHE_ID, res.json(), timeout=self.REDIS_CACHE_TTL)
                        self.add_cache(f'REDIS QUEUE:Update - {res.json()}')
                        self.send_message()
                        count = 0
                    except Exception as e:
                        self.add_cache(f'REDIS QUEUE:Update - Exception - {e}')
                except Exception as e:
                    self.add_cache(f'API:Call - Exception - {e}')

            time.sleep(1)
            count += 1

    def open(self):
        self.connection_status = True
        self.connection_text = 'API:Open - Ready'
        thread.start_new_thread(self.run_api, ())
        self.add_cache(self.connection_text)

    def close_log(self):
        self.log.close()

    def close(self):
        self.log.close()
        self.connection_status = False
        self.connection_text = f'API:Closed'
        self.add_cache(self.connection_text)

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def add_ws_client(self, ws_id):
        self.ws_clients.append(ws_id)

    def remove_ws_client(self, ws_id):
        self.ws_clients.remove(ws_id)

    def send_message(self):
        if self.REDIS_CACHE_ID in cache:
            message = cache.get(self.REDIS_CACHE_ID)
        else:
            message = f'REDIS CACHE ID: {self.REDIS_CACHE_ID} not found'

        self.add_cache(f'API:Recv - {message}')
        try:
            self.add_cache(f'WS:Send - {message}')

            for ws_id in self.ws_clients:
                common.send_ws_message(ws_id, message)

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
