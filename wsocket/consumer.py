import datetime
import json
import urllib.parse
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class JongConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope['user'].is_anonymous:
            self.close()
        else:
            self.group_name = 'wsconnection' + str(self.scope['user'].pk)
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()

    def disconnect(self, code):
        self.close()

    def notify(self, event):
        self.send(text_data=json.dumps(event))

    def receive(self, text_data=None, bytes_data=None):
        pass
