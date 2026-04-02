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
    RosterExportView,
    RoutesUploadView,
    ImportBatchDetailView,
    DailyRouteListView,
    DailyRouteDetailView,
    ImportBatchRoutesView,
    DailyRouteLinkDriverView,
    DailyRouteCreateDriverView,
    BatchSendSMSView,
    SingleRouteSendSMSView,
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

    # Legacy Roster upload/export (for backward compatibility)
    path('roster/upload/', RosterUploadView.as_view(), name='roster-upload'),
    path('roster/send-sms/', RosterSendSMSView.as_view(), name='roster-send-sms'),
    path('roster/export/', RosterExportView.as_view(), name='roster-export'),

    # New Routes management
    path('routes/upload/', RoutesUploadView.as_view(), name='routes-upload'),
    path('routes/', DailyRouteListView.as_view(), name='route-list'),
    path('routes/<int:route_id>/', DailyRouteDetailView.as_view(), name='route-detail'),
    path('routes/import/<int:batch_id>/', ImportBatchDetailView.as_view(), name='import-batch-detail'),
    path('routes/import/<int:batch_id>/routes/', ImportBatchRoutesView.as_view(), name='batch-routes'),
    path('routes/<int:route_id>/link-driver/', DailyRouteLinkDriverView.as_view(), name='route-link-driver'),
    path('routes/<int:route_id>/create-driver/', DailyRouteCreateDriverView.as_view(), name='route-create-driver'),
    path('routes/<int:route_id>/send-sms/', SingleRouteSendSMSView.as_view(), name='route-send-sms'),
    path('routes/import/<int:batch_id>/send-sms/', BatchSendSMSView.as_view(), name='batch-send-sms'),

    # SMS
    path('sms/history/', SMSHistoryView.as_view(), name='sms-history'),
    path('sms/send/', SendManualSMSView.as_view(), name='sms-send'),
    path('sms/status/', SMSWebhookView.as_view(), name='sms-webhook'),
]
