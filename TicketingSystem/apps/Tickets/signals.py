from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Ticket, TicketMessage, TicketActivity
from .middleware import get_current_user


@receiver(pre_save, sender=Ticket)
def track_ticket_changes(sender, instance, **kwargs):
    """
    Track changes to tickets made through admin panel or API.
    """
    if instance.pk:  # Only for updates, not new tickets
        try:
            old_ticket = Ticket.objects.get(pk=instance.pk)
            
            # Get the user who made the change
            user = get_current_user()
            
            if not user:
                return  # Can't track without user info
            
            # Track status changes
            if old_ticket.status != instance.status:
                TicketActivity.objects.create(
                    ticket=instance,
                    action='status_changed',
                    performed_by=user,
                    details=f'Status changed from {old_ticket.get_status_display()} to {instance.get_status_display()}'
                )
                
                # Mark resolved time if status changed to resolved
                if instance.status == 'resolved' and not instance.resolved_at:
                    from django.utils import timezone
                    instance.resolved_at = timezone.now()
                    TicketActivity.objects.create(
                        ticket=instance,
                        action='resolved',
                        performed_by=user,
                        details='Ticket marked as resolved'
                    )
            
            # Track priority changes
            if old_ticket.priority != instance.priority:
                TicketActivity.objects.create(
                    ticket=instance,
                    action='priority_changed',
                    performed_by=user,
                    details=f'Priority changed from {old_ticket.get_priority_display()} to {instance.get_priority_display()}'
                )
            
            # Track assignment changes
            if old_ticket.assigned_to != instance.assigned_to:
                assigned_to_name = instance.assigned_to.username if instance.assigned_to else 'Unassigned'
                TicketActivity.objects.create(
                    ticket=instance,
                    action='assigned_to_changed',
                    performed_by=user,
                    details=f'Ticket assigned to {assigned_to_name}'
                )
        except Ticket.DoesNotExist:
            pass


@receiver(post_save, sender=TicketMessage)
def track_message_creation(sender, instance, created, **kwargs):
    """
    Track when messages are created, especially from admin panel.
    """
    if created:  # Only for new messages
        user = get_current_user()
        
        # If we can't get the user from middleware, use the message's user
        if not user:
            user = instance.user
        
        # Create activity log for message creation
        TicketActivity.objects.create(
            ticket=instance.ticket,
            action='message_added',
            performed_by=user,
            details=f'{"Staff" if instance.is_staff_message else "User"} added a message'
        )

