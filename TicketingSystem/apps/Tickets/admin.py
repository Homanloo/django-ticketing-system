from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAttachment, TicketActivity
from .middleware import set_current_user


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'assigned_to', 'topic', 'status', 'priority', 'created_at', 'updated_at', 'resolved_at']
    list_filter = ['status', 'priority', 'created_at', 'updated_at', 'resolved_at']
    search_fields = ['id', 'user__username', 'assigned_to__username', 'topic']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """Override save_model to ensure user is tracked for activity logs."""
        set_current_user(request.user)
        super().save_model(request, obj, form, change)
        set_current_user(None)


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'is_staff_message', 'created_at')
    list_filter = ('is_staff_message', 'created_at')
    search_fields = ('ticket__id', 'message', 'user__username')
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        """Override save_model to ensure user is tracked for activity logs."""
        set_current_user(request.user)
        
        # Set the user and staff flag if this is a new message
        if not change:
            obj.user = request.user
            obj.is_staff_message = request.user.is_staff
        
        super().save_model(request, obj, form, change)
        set_current_user(None)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'ticket', 'uploaded_by', 'filesize', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'ticket__id')
    readonly_fields = ('filename', 'filesize', 'uploaded_at')
    
    def save_model(self, request, obj, form, change):
        """Override save_model to track attachment uploads and set uploader."""
        set_current_user(request.user)
        
        # Set the uploader if this is a new attachment
        if not change:
            obj.uploaded_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # Create activity log for new attachments
        if not change:
            TicketActivity.objects.create(
                ticket=obj.ticket,
                action='attachment_added',
                performed_by=request.user,
                details=f'Attachment added: {obj.filename}'
            )
        
        set_current_user(None)


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('ticket__id', 'details')
    readonly_fields = ('action', 'performed_by', 'details', 'timestamp')