import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from sectors.common import admin_config
from db.models import (
    TBLBridge,
)


class BridgeConsumer(WebsocketConsumer):
    def connect(self):
        try:
            bridge = TBLBridge.objects.get(dst_address__contains=self.scope['path'])

            self.bridge_id = bridge.id
            self.group_name = f'{admin_config.BRIDGE_CONSUMER_PREFIX}_{bridge.id}'
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()
        except Exception as e:
            self.close()

        # if self.scope['user'].is_anonymous:
        #     self.close()
        # else:
        #     self.group_name = 'wsconnection' + str(self.scope['user'].pk)
        #     async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        #     self.accept()

    def disconnect(self, code):
        self.close()

    def notify(self, event):
        del event['type']
        self.send(text_data=json.dumps(event))

    def receive(self, text_data=None, bytes_data=None):
        pass
