from django.urls import path
from .views import (
    TicketListView,
    TicketDetailView,
    TicketMessageListView,
    TicketAttachmentUploadView,
    TicketActivityListView,
    MyTicketsView,
    AssignedTicketsView,
)

app_name = 'tickets'

urlpatterns = [
    # Ticket endpoints
    path('tickets/', TicketListView.as_view(), name='ticket-list'),
    path('tickets/<uuid:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    
    # Ticket message endpoints
    path('tickets/<uuid:ticket_id>/messages/', TicketMessageListView.as_view(), name='ticket-messages'),
    
    # Ticket attachment endpoints
    path('tickets/<uuid:ticket_id>/attachments/', TicketAttachmentUploadView.as_view(), name='ticket-attachments'),
    
    # Ticket activity endpoints
    path('tickets/<uuid:ticket_id>/activities/', TicketActivityListView.as_view(), name='ticket-activities'),
    
    # User-specific ticket endpoints
    path('my-tickets/', MyTicketsView.as_view(), name='my-tickets'),
    path('assigned-tickets/', AssignedTicketsView.as_view(), name='assigned-tickets'),
]

