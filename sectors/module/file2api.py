import websocket
import _thread as thread
from django.core.cache import cache
import time
import json
from datetime import datetime

from . import common, log

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    File to API Data Bridge
    """

    def __init__(self, bridge_info):
        if admin_config.TRACE_MODE:
            websocket.enableTrace(True)

        self.bridge_info = bridge_info

        self.ws = None
        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.log = log.BridgeLog(bridge_info)
        self.cache = self.log.get_last_log()

        self.REDIS_CACHE_ID = f"{admin_config.BRIDGE_REDIS_CACHE_PREFIX}_{self.bridge_info['id']}"
        self.REDIS_CACHE_TTL = self.bridge_info['frequency']
        self.prev_file_data = None

    def dumper(self):
        count = 0
        while True:
            if not self.connection_status:
                break

            if count >= self.REDIS_CACHE_TTL:
                count = 0
                self.add_cache(f"FILE:Download - {self.bridge_info['src_address']}")
                resp_data, status_code = common.get_remote_file_data(None, self.bridge_info)
                self.add_cache(f'FILE:Recv - {resp_data}')
                if status_code < 300:
                    self.set_redis_cache(resp_data)

            time.sleep(1)
            count += 1

    def open(self):
        self.connection_status = True
        self.connection_text = 'FILE:Open - Ready'
        thread.start_new_thread(self.dumper, ())
        self.add_cache(self.connection_text)

    def close_log(self):
        self.log.close()

    def close(self):
        self.connection_status = False
        self.connection_text = f'FILE:Closed'
        self.add_cache(self.connection_text)

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def set_redis_cache(self, message):
        try:
            if not message:
                self.add_cache(f'REDIS QUEUE:Append - Ignored! - Empty Data!')
                return

            bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
            if bridge.is_status == 1:
                self.add_cache(f'REDIS QUEUE:Append - Ignored! - Out of Funds!')
                return

            new_message = message
            if self.prev_file_data:
                new_message = common.get_diff_lists(None, self.prev_file_data, message)
                if not new_message:
                    self.add_cache(f'REDIS QUEUE:Append - Ignored! - Same Data!')
                    return

            if self.REDIS_CACHE_ID not in cache:
                cache.set(self.REDIS_CACHE_ID, [])

            cache_data = cache.get(self.REDIS_CACHE_ID)
            cache_data.append({
                'date': datetime.utcnow().strftime('%m/%d/%Y, %H:%M:%S'),
                'data': new_message
            })

            cache.set(self.REDIS_CACHE_ID, cache_data)
            self.add_cache(f'REDIS QUEUE:Append - {new_message}')

            self.prev_file_data = message
        except Exception as e:
            self.add_cache(f'REDIS QUEUE:Append - Exception - {e}')

    def add_cache(self, data):
        self.trace(data)

        if len(self.cache) > admin_config.LOCAL_CACHE_LIMIT:
            self.cache.pop(0)

        cache_data = {
            'date': datetime.utcnow().strftime('%m/%d/%Y, %H:%M:%S'),
            'data': data
        }

        self.cache.append(cache_data)

        self.log.write_log(json.dumps(cache_data))

    def get_cache(self):
        return self.cache

    def trace(self, trace_log):
        if admin_config.TRACE_MODE:
            print(f"{datetime.utcnow()}: {self.bridge_info['name']}_{self.bridge_info['user_id']}: {trace_log}")
