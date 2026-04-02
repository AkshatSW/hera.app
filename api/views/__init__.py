from .driver_views import DriverListView, DriverDetailView
from .vehicle_views import VehicleListView, VehicleDetailView
from .assignment_views import AssignmentListView, AssignmentDetailView
from .roster_views import RosterUploadView, RosterSendSMSView, RosterExportView
from .routes_views import (
    RoutesUploadView,
    ImportBatchDetailView,
    DailyRouteListView,
    DailyRouteDetailView,
    ImportBatchRoutesView,
    DailyRouteLinkDriverView,
    DailyRouteCreateDriverView,
    BatchSendSMSView,
    SingleRouteSendSMSView,
)
from .sms_views import SMSHistoryView, SendManualSMSView, SMSWebhookView
from .dashboard_views import dashboard_view, associates_view, vehicles_view, sms_center_view, import_review_view
from .auth_views import (
    login_view, logout_view, signup_view, verify_email_view,
    resend_otp_view, forgot_password_view, reset_password_view,
)

__all__ = [
    'DriverListView', 'DriverDetailView',
    'VehicleListView', 'VehicleDetailView',
    'AssignmentListView', 'AssignmentDetailView',
    'RosterUploadView', 'RosterSendSMSView', 'RosterExportView',
    'RoutesUploadView', 'ImportBatchDetailView', 'DailyRouteListView', 'DailyRouteDetailView', 'ImportBatchRoutesView',
    'DailyRouteLinkDriverView', 'DailyRouteCreateDriverView', 'BatchSendSMSView', 'SingleRouteSendSMSView',
    'SMSHistoryView', 'SendManualSMSView', 'SMSWebhookView',
    'dashboard_view', 'associates_view', 'vehicles_view', 'sms_center_view', 'import_review_view',
    'login_view', 'logout_view', 'signup_view', 'verify_email_view',
    'resend_otp_view', 'forgot_password_view', 'reset_password_view',
]
