import websocket
import _thread as thread
import time
import requests
import json
from datetime import datetime

from sectors.common import admin_config

from db.models import (
    TBLBridge,
)


class Bridge:
    """
    WebSocket to WebHook Data Bridge
    """

    def __init__(self, bridge_info):
        if admin_config.TRACE_MODE:
            websocket.enableTrace(True)

        self.bridge_info = bridge_info

        self.ws = None
        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.cache = []

    def run_forever(self):
        self.ws.run_forever()

    def open(self):
        if self.ws is None:
            self.ws = websocket.WebSocketApp(self.bridge_info['src_address'],
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
        if not self.connection_status:
            thread.start_new_thread(self.run_forever, ())

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
        self.add_cache(f'WS:Send - {message}')
        try:
            self.ws.send(message)
        except Exception as e:
            self.add_cache(f'WS:Send - Exception - {e}')

    def on_message(self, ws, message):
        self.add_cache(f'WS:Recv - {message}')
        self.call_webhook(message)

    def on_error(self, ws, error):
        self.connection_status = False
        self.connection_text = f'WS:Error - {error}'
        self.add_cache(self.connection_text)

    def on_close(self, ws, close_status_code, close_msg):
        self.connection_status = False
        self.connection_text = f'WS:Closed - {close_status_code} - {close_msg}'
        self.add_cache(self.connection_text)

    def call_webhook(self, message):
        wh_address = self.bridge_info['dst_address']

        content = {'content': message}
        format_json = json.loads(self.bridge_info['format'])
        search_word = format_json['search_word']
        replace_word = format_json['replace_word']
        any = format_json['any']

        if search_word:
            replaceable = False
            if any:
                search_word_array = search_word.split(',')
                for sw in search_word_array:
                    if sw.strip() in message:
                        replaceable = True
                        break
            else:
                if search_word in message:
                    replaceable = True

            if replaceable:
                try:
                    content = json.loads(replace_word)
                except:
                    content = {'content': replace_word}

        # call WebHook
        try:
            self.add_cache(f'WH:Send - {content}')
            res = requests.post(wh_address, json=content)
            response = {
                'status_code': res.status_code,
                'text': res.text
            }
            self.add_cache(f'WH:Recv - {response}')
        except Exception as e:
            self.add_cache(f'WH:Send - Exception - {e}')

        bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
        bridge.api_calls += 1
        bridge.save()

    def add_cache(self, data):
        self.trace(data)

        if len(self.cache) > admin_config.LOCAL_CACHE_LIMIT:
            self.cache.pop(0)

        self.cache.append({
            'date': datetime.now(),
            'data': data
        })

    def get_cache(self):
        return self.cache

    def trace(self, log):
        if admin_config.TRACE_MODE:
            print(f"{datetime.now()}: {self.bridge_info['name']}_{self.bridge_info['user_id']}: {log}")
