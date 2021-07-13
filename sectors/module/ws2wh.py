import websocket
import _thread as thread
import time
import requests
import json

from db.models import (
    TBLBridge,
)


class Bridge:
    """
    WebSocket to WebHook Data Bridge
    """

    def __init__(self, bridge_info):
        websocket.enableTrace(True)

        self.bridge_info = bridge_info

        self.ws = None
        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.message_cache = []
        self.third_response = None

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
        self.ws.close()

    def is_connected(self):
        while self.connection_status is None:
            time.sleep(0.1)

        return self.connection_status

    def on_open(self, ws):
        self.connection_status = True
        self.connection_text = 'Connected'

    def on_message(self, ws, message):
        # self.message_cache.append(message)
        self.call_webhook(message)

    def on_error(self, ws, error):
        self.connection_status = False
        self.connection_text = f'Error - {error}'

    def on_close(self, ws, close_status_code, close_msg):
        self.connection_status = False
        self.connection_text = f'Closed - {close_status_code} - {close_msg}'

    def call_webhook(self, message):
        wh_address = self.bridge_info['dst_address']
        format = self.bridge_info['format']

        content = {'content': message}

        if format:
            format_json = json.loads(format)
            search_word = format_json['search_word']
            replace_word = format_json['replace_word']

            search_word_array = search_word.split(',')
            for sw in search_word_array:
                if sw.strip() in content:
                    content = json.loads(replace_word)
                    break

        # call webhook
        res = requests.post(wh_address, json=content)
        self.third_response = {
            'status_code': res.status_code,
            'text': res.text
        }

        bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
        bridge.api_calls += 1
        bridge.third_response = json.dumps(self.third_response)
        bridge.save()
