from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Ticket, TicketMessage, TicketAttachment, TicketActivity
from apps.Users.models import Order

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'created_at']
        read_only_fields = ['id', 'order_number', 'status', 'created_at']


class TicketAttachmentSerializer(serializers.ModelSerializer):

    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = [
            'id', 'ticket', 'message', 'file', 'file_url',
            'filename', 'filesize', 'uploaded_at', 'uploaded_by'
        ]
        read_only_fields = ['id', 'filename', 'filesize', 'uploaded_at', 'uploaded_by']

    def get_file_url(self, obj):
        """
        Get the absolute URL for the file.
        """
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class TicketMessageSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = [
            'id', 'ticket', 'user', 'message',
            'is_staff_message', 'created_at', 'attachments'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'is_staff_message']


class TicketMessageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TicketMessage
        fields = ['ticket', 'message']


class TicketActivitySerializer(serializers.ModelSerializer):

    performed_by = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = TicketActivity
        fields = [
            'id', 'ticket', 'action', 'action_display',
            'performed_by', 'details', 'timestamp'
        ]
        read_only_fields = ['id', 'performed_by', 'timestamp']


class TicketListSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'assigned_to', 'topic', 'status',
            'status_display', 'priority', 'priority_display',
            'created_at', 'updated_at', 'message_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        """
        Get the count of messages for this ticket.
        """
        return obj.messages.count()


class TicketDetailSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    activities = TicketActivitySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'order', 'assigned_to', 'topic', 'description',
            'status', 'status_display', 'priority', 'priority_display',
            'created_at', 'updated_at', 'resolved_at',
            'messages', 'attachments', 'activities'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class TicketCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = [
            'order', 'topic', 'description'
        ]

    def validate_description(self, value):
        """
        Validate that description is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value

    def validate_topic(self, value):
        """
        Validate that topic is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        return value
    
    def validate_order(self, value):
        """
        Validate that the order belongs to the user creating the ticket.
        """
        if value:
            request = self.context.get('request')
            if request and value.user != request.user:
                raise serializers.ValidationError("You can only create tickets for your own orders.")
        return value


class TicketUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = [
            'topic', 'description', 'status', 'priority',
            'assigned_to', 'resolved_at'
        ]

    def validate_status(self, value):
        """
        Validate status transitions.
        """
        if self.instance:
            old_status = self.instance.status
            if old_status == 'closed' and value != 'closed':
                raise serializers.ValidationError(
                    "Cannot reopen a closed ticket. Please create a new ticket."
                )
        return value

