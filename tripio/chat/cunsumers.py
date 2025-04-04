import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user_id = text_data_json['user_id']
        
        # Save message to database
        message_obj = await self.save_message(user_id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'message_id': str(message_obj.id),
                'created_at': message_obj.created_at.isoformat(),
            }
        )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'created_at': event['created_at'],
        }))
    
    @database_sync_to_async
    def save_message(self, user_id, message_content):
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=message_content
        )
        
        return message
    
    @database_sync_to_async
    def mark_messages_as_read(self, user_id):
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        # Mark all messages from the other user as read
        now = timezone.now()
        Message.objects.filter(
            conversation=conversation,
            sender__id=user_id,
            is_read=False
        ).update(is_read=True, read_at=now)