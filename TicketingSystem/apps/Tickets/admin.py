from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAttachment, TicketActivity


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'assigned_to', 'topic', 'status', 'priority', 'created_at', 'updated_at', 'resolved_at']
    list_filter = ['status', 'priority', 'created_at', 'updated_at', 'resolved_at']
    search_fields = ['id', 'user__username', 'assigned_to__username', 'topic']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'is_staff_message', 'created_at')
    list_filter = ('is_staff_message', 'created_at')
    search_fields = ('ticket__id', 'message', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'ticket', 'uploaded_by', 'filesize', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'ticket__id')
    readonly_fields = ('filename', 'filesize', 'uploaded_at')


@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('ticket__id', 'details')
    readonly_fields = ('action', 'performed_by', 'details', 'timestamp')