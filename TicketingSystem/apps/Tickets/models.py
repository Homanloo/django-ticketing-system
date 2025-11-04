from django.db import models
from django.contrib.auth.models import User
from apps.Users.models import Order
from django.utils import timezone
import uuid


class Ticket(models.Model):
    """
    A model for a ticket in the ticketing system.
    """

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_tickets', null=True, blank=True)
    topic = models.CharField(max_length=255)
    description = models.TextField(max_length=10000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='low')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.topic}"

    class Meta:
        ordering = ['-created_at']


class TicketMessage(models.Model):
    """
    Coversation between a user and an agent.
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField(max_length=10000)
    is_staff_message = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message #{self.id} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket Message'
        verbose_name_plural = 'Ticket Messages'

class TicketAttachment(models.Model):
    """
    Attachment to a ticket message.
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='ticket_attachments/')
    filename = models.CharField(max_length=255)
    filesize = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_attachments')

    def __str__(self):
        return f"Attachment #{self.id} - {self.filename}"
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Ticket Attachment'
        verbose_name_plural = 'Ticket Attachments'

    def save(self, *args, **kwargs):
        if self.file:
            self.filesize = self.file.size
            self.filename = self.file.name
        super().save(*args, **kwargs)


class TicketActivity(models.Model):
    """
    Activity log for a ticket to track all changes.
    """

    ACTION_CHOICES = [
        ('created', 'Ticket Created'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('message_added', 'Message Added'),
        ('attachment_added', 'Attachment Added'),
        ('assigned_to_changed', 'Assigned To Changed'),
        ('resolved', 'Ticket Resolved'),
        ('closed', 'Ticket Closed'),
        ('deleted', 'Ticket Deleted'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    details = models.TextField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Activity #{self.id} - {self.performed_by.username} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Ticket Activity'
        verbose_name_plural = 'Ticket Activities'
