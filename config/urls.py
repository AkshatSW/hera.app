from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import (
    dashboard_view, associates_view, vehicles_view, sms_center_view,
    login_view, logout_view, signup_view, verify_email_view,
    resend_otp_view, forgot_password_view, reset_password_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # Auth
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('verify-email/', verify_email_view, name='verify-email'),
    path('resend-otp/', resend_otp_view, name='resend-otp'),
    path('forgot-password/', forgot_password_view, name='forgot-password'),
    path('reset-password/', reset_password_view, name='reset-password'),

    # Dashboard (authenticated)
    path('', dashboard_view, name='dashboard'),
    path('associates/', associates_view, name='associates'),
    path('vehicles/', vehicles_view, name='vehicles'),
    path('sms/', sms_center_view, name='sms-center'),
]

if settings.DEBUG and settings.STATICFILES_DIRS:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
