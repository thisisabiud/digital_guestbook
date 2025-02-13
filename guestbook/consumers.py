# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers.json import DjangoJSONEncoder
from guestbook.models import GuestbookEntry

class GuestbookConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get event_id from URL route
        self.event_id = self.scope['url_route']['kwargs'].get('event_id')

        # Join appropriate group
        self.group_name = f"guestbook_{self.event_id}" if self.event_id else "guestbook_all"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle messages from WebSocket clients"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'request_messages':
                # Send current messages to the client
                messages = await self.get_messages()
                await self.send(text_data=json.dumps({
                    'type': 'message_list',
                    'messages': messages
                }, cls=DjangoJSONEncoder))
        except json.JSONDecodeError:
            pass

    async def message_update(self, event):
        """Handle new message notifications"""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }, cls=DjangoJSONEncoder))

    @database_sync_to_async
    def get_messages(self):
        """Get messages for the current event"""
        query = GuestbookEntry.objects.all()
        if self.event_id:
            query = query.filter(event_id=self.event_id)
        
        return list(query.order_by('-created_at').values(
            'id', 
            'signature_base64',
            'created_at'
        ))