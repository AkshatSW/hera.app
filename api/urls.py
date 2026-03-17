from django.urls import path
from api.views import (
    DriverListView,
    DriverDetailView,
    VehicleListView,
    VehicleDetailView,
    AssignmentListView,
    AssignmentDetailView,
    RosterUploadView,
    RosterSendSMSView,
    SMSHistoryView,
    SendManualSMSView,
    SMSWebhookView,
)

urlpatterns = [
    # Drivers
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('drivers/<int:pk>/', DriverDetailView.as_view(), name='driver-detail'),

    # Vehicles
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),

    # Assignments
    path('assignments/', AssignmentListView.as_view(), name='assignment-list'),
    path('assignments/<int:pk>/', AssignmentDetailView.as_view(), name='assignment-detail'),

    # Roster upload
    path('roster/upload/', RosterUploadView.as_view(), name='roster-upload'),
    path('roster/send-sms/', RosterSendSMSView.as_view(), name='roster-send-sms'),

    # SMS
    path('sms/history/', SMSHistoryView.as_view(), name='sms-history'),
    path('sms/send/', SendManualSMSView.as_view(), name='sms-send'),
    path('sms/status/', SMSWebhookView.as_view(), name='sms-webhook'),
]
