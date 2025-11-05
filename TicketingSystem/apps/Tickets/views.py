from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from .models import Ticket, TicketMessage, TicketAttachment, TicketActivity
from apps.Users.models import Order
from .serializers import (
    TicketListSerializer,
    TicketDetailSerializer,
    TicketCreateSerializer,
    TicketUpdateSerializer,
    TicketMessageSerializer,
    TicketMessageCreateSerializer,
    TicketAttachmentSerializer,
    TicketActivitySerializer,
    OrderSerializer,
)


class TicketListView(APIView):
    """
    List all tickets or create a new ticket.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_tickets',
        summary='List All Tickets',
        description='Get a list of all tickets for the authenticated user.',
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by status (open, in_progress, resolved, closed)',
                required=False
            ),
            OpenApiParameter(
                name='priority',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by priority (low, medium, high, critical)',
                required=False
            ),
        ],
        responses={
            200: TicketListSerializer(many=True),
        }
    )
    def get(self, request):
        # Get base queryset
        if request.user.is_staff:
            tickets = Ticket.objects.all()
        else:
            tickets = Ticket.objects.filter(user=request.user)
        
        # Apply filters
        status_filter = request.query_params.get('status', None)
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        
        priority_filter = request.query_params.get('priority', None)
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        
        serializer = TicketListSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id='create_ticket',
        summary='Create New Ticket',
        description='Create a new support ticket.',
        request=TicketCreateSerializer,
        responses={
            201: TicketDetailSerializer,
            400: {'description': 'Bad request'},
        }
    )
    def post(self, request):
        serializer = TicketCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ticket = serializer.save(user=request.user)
            
            # Create activity log for ticket creation
            TicketActivity.objects.create(
                ticket=ticket,
                action='created',
                performed_by=request.user,
                details=f'Ticket created with topic: {ticket.topic}'
            )
            
            detail_serializer = TicketDetailSerializer(ticket)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketDetailView(APIView):
    """
    Retrieve, update or delete a ticket.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='get_ticket',
        summary='Get Ticket Details',
        description='Get detailed information about a specific ticket.',
        responses={
            200: TicketDetailSerializer,
            404: {'description': 'Ticket not found'},
        }
    )
    def get(self, request, pk):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=pk)
            else:
                ticket = Ticket.objects.get(pk=pk, user=request.user)
            serializer = TicketDetailSerializer(ticket)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        operation_id='update_ticket',
        summary='Update Ticket',
        description='Update ticket information.',
        request=TicketUpdateSerializer,
        responses={
            200: TicketDetailSerializer,
            400: {'description': 'Bad request'},
            404: {'description': 'Ticket not found'},
        }
    )
    def put(self, request, pk):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=pk)
            else:
                ticket = Ticket.objects.get(pk=pk, user=request.user)
            
            # Store old values for activity log
            old_status = ticket.status
            old_priority = ticket.priority
            old_assigned_to = ticket.assigned_to
            
            serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
            if serializer.is_valid():
                updated_ticket = serializer.save()
                
                # Create activity logs for changes
                if old_status != updated_ticket.status:
                    TicketActivity.objects.create(
                        ticket=updated_ticket,
                        action='status_changed',
                        performed_by=request.user,
                        details=f'Status changed from {old_status} to {updated_ticket.status}'
                    )
                    
                    # Mark resolved time if status changed to resolved
                    if updated_ticket.status == 'resolved' and not updated_ticket.resolved_at:
                        updated_ticket.resolved_at = timezone.now()
                        updated_ticket.save()
                        TicketActivity.objects.create(
                            ticket=updated_ticket,
                            action='resolved',
                            performed_by=request.user,
                            details='Ticket marked as resolved'
                        )
                
                if old_priority != updated_ticket.priority:
                    TicketActivity.objects.create(
                        ticket=updated_ticket,
                        action='priority_changed',
                        performed_by=request.user,
                        details=f'Priority changed from {old_priority} to {updated_ticket.priority}'
                    )
                
                if old_assigned_to != updated_ticket.assigned_to:
                    assigned_to_name = updated_ticket.assigned_to.username if updated_ticket.assigned_to else 'Unassigned'
                    TicketActivity.objects.create(
                        ticket=updated_ticket,
                        action='assigned_to_changed',
                        performed_by=request.user,
                        details=f'Ticket assigned to {assigned_to_name}'
                    )
                
                detail_serializer = TicketDetailSerializer(updated_ticket)
                return Response(detail_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to update it"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        operation_id='delete_ticket',
        summary='Delete Ticket',
        description='Delete a ticket (staff only).',
        responses={
            200: {'description': 'Ticket deleted successfully'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Ticket not found'},
        }
    )
    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff members can delete tickets"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            ticket = Ticket.objects.get(pk=pk)
            
            # Create activity log before deletion
            TicketActivity.objects.create(
                ticket=ticket,
                action='deleted',
                performed_by=request.user,
                details=f'Ticket deleted: {ticket.topic}'
            )
            
            ticket.delete()
            return Response(
                {"message": "Ticket deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class TicketMessageListView(APIView):
    """
    List all messages for a ticket or add a new message.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_ticket_messages',
        summary='List Ticket Messages',
        description='Get all messages for a specific ticket.',
        responses={
            200: TicketMessageSerializer(many=True),
            404: {'description': 'Ticket not found'},
        }
    )
    def get(self, request, ticket_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            messages = ticket.messages.all().order_by('created_at')
            serializer = TicketMessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        operation_id='create_ticket_message',
        summary='Add Message to Ticket',
        description='Add a new message to a ticket.',
        request=TicketMessageCreateSerializer,
        responses={
            201: TicketMessageSerializer,
            400: {'description': 'Bad request'},
            404: {'description': 'Ticket not found'},
        }
    )
    def post(self, request, ticket_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            serializer = TicketMessageCreateSerializer(data={'ticket': ticket.id, 'message': request.data.get('message')})
            if serializer.is_valid():
                message = serializer.save(
                    user=request.user,
                    is_staff_message=request.user.is_staff
                )
                
                # Activity log is automatically created by the signal
                
                detail_serializer = TicketMessageSerializer(message)
                return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )


class TicketAttachmentUploadView(APIView):
    """
    Upload or list attachments for a ticket.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_ticket_attachments',
        summary='List Ticket Attachments',
        description='Get all attachments for a specific ticket.',
        responses={
            200: TicketAttachmentSerializer(many=True),
            404: {'description': 'Ticket not found'},
        }
    )
    def get(self, request, ticket_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            attachments = ticket.attachments.all().order_by('-uploaded_at')
            serializer = TicketAttachmentSerializer(attachments, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        operation_id='upload_ticket_attachment',
        summary='Upload Attachment',
        description='Upload a file attachment to a ticket.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'message_id': {'type': 'string', 'format': 'uuid', 'required': False},
                }
            }
        },
        responses={
            201: TicketAttachmentSerializer,
            400: {'description': 'Bad request'},
            404: {'description': 'Message not found'},
        }
    )
    def post(self, request, ticket_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            file = request.FILES.get('file')
            
            if not file:
                return Response(
                    {"error": "File is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Message is optional - can attach directly to ticket
            message = None
            message_id = request.data.get('message_id')
            if message_id:
                try:
                    message = TicketMessage.objects.get(pk=message_id, ticket=ticket)
                except TicketMessage.DoesNotExist:
                    return Response(
                        {"error": "Message not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            attachment = TicketAttachment.objects.create(
                ticket=ticket,
                message=message,
                file=file,
                uploaded_by=request.user
            )
            
            # Create activity log
            TicketActivity.objects.create(
                ticket=ticket,
                action='attachment_added',
                performed_by=request.user,
                details=f'Attachment added: {attachment.filename}'
            )
            
            serializer = TicketAttachmentSerializer(attachment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )


class TicketAttachmentDeleteView(APIView):
    """
    Delete a ticket attachment.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='delete_ticket_attachment',
        summary='Delete Attachment',
        description='Delete a file attachment from a ticket.',
        responses={
            200: {'description': 'Attachment deleted successfully'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Attachment not found'},
        }
    )
    def delete(self, request, ticket_id, attachment_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            try:
                attachment = TicketAttachment.objects.get(pk=attachment_id, ticket=ticket)
            except TicketAttachment.DoesNotExist:
                return Response(
                    {"error": "Attachment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Only the uploader or staff can delete
            if attachment.uploaded_by != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to delete this attachment"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            filename = attachment.filename
            attachment.delete()
            
            # Create activity log
            TicketActivity.objects.create(
                ticket=ticket,
                action='attachment_added',  # Using existing action
                performed_by=request.user,
                details=f'Attachment deleted: {filename}'
            )
            
            return Response(
                {"message": "Attachment deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )


class TicketActivityListView(APIView):
    """
    List all activities for a ticket.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_ticket_activities',
        summary='List Ticket Activities',
        description='Get all activity logs for a specific ticket.',
        responses={
            200: TicketActivitySerializer(many=True),
            404: {'description': 'Ticket not found'},
        }
    )
    def get(self, request, ticket_id):
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, user=request.user)
            
            activities = ticket.activities.all()
            serializer = TicketActivitySerializer(activities, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found or you don't have permission to access it"},
                status=status.HTTP_404_NOT_FOUND
            )


class MyTicketsView(APIView):
    """
    List all tickets for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_my_tickets',
        summary='List My Tickets',
        description='Get all tickets created by the authenticated user.',
        responses={
            200: TicketListSerializer(many=True),
        }
    )
    def get(self, request):
        tickets = Ticket.objects.filter(user=request.user)
        serializer = TicketListSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignedTicketsView(APIView):
    """
    List all tickets assigned to the authenticated staff member.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_assigned_tickets',
        summary='List Assigned Tickets',
        description='Get all tickets assigned to the authenticated staff member.',
        responses={
            200: TicketListSerializer(many=True),
            403: {'description': 'Permission denied - staff only'},
        }
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff members can access assigned tickets"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tickets = Ticket.objects.filter(assigned_to=request.user)
        serializer = TicketListSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserOrdersView(APIView):
    """
    List all orders for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id='list_user_orders',
        summary='List User Orders',
        description='Get all orders for the authenticated user to select when creating a ticket.',
        responses={
            200: OrderSerializer(many=True),
        }
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
