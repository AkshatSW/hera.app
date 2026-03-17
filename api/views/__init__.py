from .driver_views import DriverListView, DriverDetailView
from .vehicle_views import VehicleListView, VehicleDetailView
from .assignment_views import AssignmentListView, AssignmentDetailView
from .roster_views import RosterUploadView, RosterSendSMSView
from .sms_views import SMSHistoryView, SendManualSMSView, SMSWebhookView
from .dashboard_views import dashboard_view, associates_view, vehicles_view, sms_center_view
from .auth_views import (
    login_view, logout_view, signup_view, verify_email_view,
    resend_otp_view, forgot_password_view, reset_password_view,
)

__all__ = [
    'DriverListView', 'DriverDetailView',
    'VehicleListView', 'VehicleDetailView',
    'AssignmentListView', 'AssignmentDetailView',
    'RosterUploadView', 'RosterSendSMSView',
    'SMSHistoryView', 'SendManualSMSView', 'SMSWebhookView',
    'dashboard_view', 'associates_view', 'vehicles_view', 'sms_center_view',
    'login_view', 'logout_view', 'signup_view', 'verify_email_view',
    'resend_otp_view', 'forgot_password_view', 'reset_password_view',
]
