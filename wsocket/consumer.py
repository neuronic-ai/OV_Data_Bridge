import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from sectors.common import admin_config, common
from db.models import (
    TBLBridge
)


class BridgeConsumer(WebsocketConsumer):
    def connect(self):
        try:
            bridge = TBLBridge.objects.get(dst_address__contains=self.scope['path'], is_active=True)

            self.bridge_id = bridge.id
            self.group_name = f'{admin_config.BRIDGE_CONSUMER_PREFIX}_{bridge.id}_{common.generate_random_string(6)}'
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()

            admin_config.BRIDGE_HANDLE.add_ws_client(self.bridge_id, self.group_name)
        except:
            self.close()

        # if self.scope['user'].is_anonymous:
        #     self.close()
        # else:
        #     self.group_name = 'wsconnection' + str(self.scope['user'].pk)
        #     async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        #     self.accept()

    def disconnect(self, code):
        self.close()
        try:
            admin_config.BRIDGE_HANDLE.remove_ws_client(self.bridge_id, self.group_name)
        except:
            pass

    def notify(self, event):
        del event['type']
        self.send(text_data=json.dumps(event))

    def receive(self, text_data=None, bytes_data=None):
        pass
