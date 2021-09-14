import _thread as thread
import time
from datetime import datetime
import json

from . import log, file

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    WebHook to File Data Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.log = log.BridgeLog(bridge_info)
        self.cache = self.log.get_last_log()

        self.file = file.File(bridge_info['dst_address'], bridge_info['file_format'])

        self.flush = self.bridge_info['flush']

    def notify_event(self, event):
        data = event['data']
        if event['type'] == 'on_message':
            self.write_file(data['message'])

    def run_api(self):
        count = 0
        while True:
            if not self.connection_status:
                break

            if count >= self.flush:
                count = 0
                self.file.truncate()

            time.sleep(1)
            count += 1

    def open(self):
        self.connection_status = True
        self.connection_text = 'WH:Open - Ready'
        thread.start_new_thread(self.run_api, ())
        self.add_cache(self.connection_text)

    def close_log(self):
        self.log.close()

    def close(self):
        self.connection_status = False
        self.connection_text = f'WH:Closed'
        self.add_cache(self.connection_text)

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def write_file(self, message):
        self.add_cache(f'WH:Recv - {message}')
        self.add_cache(f'FILE:Update - {message}')
        self.file.write(message)

        bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
        bridge.api_calls += 1
        bridge.save()

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
