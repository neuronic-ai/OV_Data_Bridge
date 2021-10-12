import _thread as thread
import time
import requests
from datetime import datetime
import json

from . import common, log

from sectors.common import admin_config

from db.models import (
    TBLBridge
)


class Bridge:
    """
    File to WebHook Data Bridge
    """

    def __init__(self, bridge_info):
        self.bridge_info = bridge_info

        self.connection_status = None
        self.connection_text = 'Waiting for connect'
        self.log = log.BridgeLog(bridge_info)
        self.cache = self.log.get_last_log()
        self.ws_clients = []

        self.FILE_FREQUENCY = self.bridge_info['frequency']
        self.prev_file_data = None

    def run_download(self):
        count = 0
        while True:
            if not self.connection_status:
                break

            if count == 0 or count >= self.FILE_FREQUENCY:
                count = 0
                self.add_cache(f"FILE:Download - {self.bridge_info['src_address']}")
                resp_data, status_code = common.get_remote_file_data(None, self.bridge_info)
                self.add_cache(f'FILE:Recv - {resp_data}')
                if status_code < 300:
                    self.call_webhook(resp_data)

            time.sleep(1)
            count += 1

    def open(self):
        self.connection_status = True
        self.connection_text = 'FILE:Open - Ready'
        thread.start_new_thread(self.run_download, ())
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

    def call_webhook(self, message):
        if not message:
            self.add_cache(f'WS:Send - Ignored! - Empty Data!')
            return

        bridge = TBLBridge.objects.get(id=self.bridge_info['id'])
        if bridge.is_status == 1:
            self.add_cache(f'WH:Send - Ignored! - Out of Funds!')
            return

        new_message = message
        if self.prev_file_data:
            new_message = common.get_diff_lists(None, self.prev_file_data, message)
            if not new_message:
                self.add_cache(f'WH:Send - Ignored! - Same Data!')
                return

        wh_address = self.bridge_info['dst_address']
        replaceable, content = common.get_formatted_content(new_message, self.bridge_info)

        if replaceable:
            # call WebHook
            try:
                self.add_cache(f'WH:Send - {content}')
                res = requests.post(wh_address, json={'content': json.dumps(content)}, verify=False)
                response = {
                    'status_code': res.status_code,
                    'text': res.text
                }
                self.add_cache(f'WH:Recv - {response}')
            except Exception as e:
                self.add_cache(f'WH:Send - Exception - {e}')

            bridge.api_calls += 1
            bridge.save()

            self.prev_file_data = message
        else:
            self.add_cache(f'WH:Send - Ignored! - Format!')

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
