import websocket
import _thread as thread
import time
import json
import requests
from datetime import datetime

from . import common, log, file

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    WebSocket to File Data Bridge
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

        self.file = file.File(bridge_info['dst_address'], bridge_info['file_format'])

        self.flush = self.bridge_info['flush']

    def run_forever(self):
        self.ws.run_forever()

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
        if self.ws is None:
            self.ws = websocket.WebSocketApp(self.bridge_info['src_address'],
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
        if not self.connection_status:
            thread.start_new_thread(self.run_forever, ())
            thread.start_new_thread(self.run_api, ())

    def close_log(self):
        self.log.close()

    def close(self):
        self.connection_status = False
        self.ws.close()

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def on_open(self, ws):
        self.connection_status = True
        self.connection_text = 'WS:Open - Connected'
        self.add_cache(self.connection_text)

    def send_message(self, message):
        if self.connection_status:
            self.add_cache(f'WS:Send - {message}')
            try:
                self.ws.send(message)
            except Exception as e:
                self.add_cache(f'WS:Send - Exception - {e}')

    def on_message(self, ws, message):
        if self.connection_status:
            self.add_cache(f'WS:Recv - {message}')
            self.write_file(message)

    def on_error(self, ws, error):
        self.connection_status = False
        self.connection_text = f'WS:Error - {error}'
        self.add_cache(self.connection_text)

    def on_close(self, ws, close_status_code, close_msg):
        self.connection_status = False
        self.connection_text = f'WS:Closed - {close_status_code} - {close_msg}'
        self.add_cache(self.connection_text)

    def write_file(self, message):
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
