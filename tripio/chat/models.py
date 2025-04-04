from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

class Conversation(models.Model):
    """
    A conversation between two users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The two participants in the conversation
    initiator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='initiated_conversations', verbose_name=_('initiator'))
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='received_conversations', verbose_name=_('receiver'))
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # If this is related to a specific package
    package = models.ForeignKey('packages.Package', on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='conversations',
                              verbose_name=_('package'))
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']
        # Ensure we don't have duplicate conversations between the same users
        unique_together = [('initiator', 'receiver', 'package')]
    
    def __str__(self):
        return f"Conversation between {self.initiator.username} and {self.receiver.username}"
    
    def get_other_user(self, user):
        """
        Return the other user in the conversation.
        """
        if user == self.initiator:
            return self.receiver
        return self.initiator

class Message(models.Model):
    """
    A message within a conversation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, 
                                    related_name='messages', verbose_name=_('conversation'))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                             related_name='sent_messages', verbose_name=_('sender'))
    content = models.TextField(_('content'))
    
    # For sending images or files
    attachment = models.FileField(_('attachment'), upload_to='chat_attachments/', null=True, blank=True)
    
    # Status tracking
    is_read = models.BooleanField(_('read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        # Update the conversation's updated_at timestamp
        self.conversation.updated_at = self.created_at
        self.conversation.save(update_fields=['updated_at'])
        super().save(*args, **kwargs)

class MessageTemplate(models.Model):
    """
    Predefined message templates for sellers to respond quickly.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                           related_name='message_templates', verbose_name=_('user'))
    title = models.CharField(_('title'), max_length=100)
    content = models.TextField(_('content'))
    
    class Meta:
        verbose_name = _('message template')
        verbose_name_plural = _('message templates')
        ordering = ['title']
        unique_together = [('user', 'title')]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"