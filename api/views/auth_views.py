import re
import logging
import requests as http_requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from api.models import EmailOTP
from api.services.email_service import send_otp_sms

User = get_user_model()
logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """Normalize phone number to E.164 format (only + and digits)."""
    cleaned = re.sub(r'[^\d]', '', phone)
    if phone.startswith('+'):
        return '+' + cleaned
    return '+' + cleaned


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    errors = {}
    form_data = {}

    if request.method == 'POST':
        dsp_name = request.POST.get('dsp_name', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        country_code = request.POST.get('country_code', '+1').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        recaptcha_response = request.POST.get('g-recaptcha-response', '')

        phone = normalize_phone(country_code + phone_number)

        form_data = {
            'dsp_name': dsp_name, 'first_name': first_name,
            'last_name': last_name, 'country_code': country_code,
            'phone_number': phone_number, 'email': email,
        }

        if not all([dsp_name, first_name, last_name, phone_number, password]):
            errors['general'] = 'All required fields must be filled.'
        elif password != password_confirm:
            errors['password_confirm'] = 'Passwords do not match.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'
        elif User.objects.filter(phone=phone).exists():
            errors['phone'] = 'An account with this phone number already exists.'

        if not errors and settings.RECAPTCHA_SECRET_KEY:
            recap_result = http_requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response,
                },
            )
            if not recap_result.json().get('success'):
                errors['recaptcha'] = 'Please complete the reCAPTCHA.'

        if not errors:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        dsp_name=dsp_name,
                    )
                    otp = EmailOTP(user=user, purpose='verification')
                    otp.save()

                send_otp_sms(user.phone, otp.code, purpose='verification')
                request.session['pending_verification_user_id'] = user.id
                return redirect('verify-email')
            except Exception as e:
                logger.error(f"Signup error: {e}")
                errors['general'] = 'An error occurred. Please try again.'

    return render(request, 'dashboard/signup.html', {
        'errors': errors,
        'form_data': form_data,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def verify_email_view(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    if user.is_verified:
        return redirect('login')

    error = None
    if request.method == 'POST':
        code = request.POST.get('otp_code', '').strip()

        # Use atomic update to prevent race condition
        with transaction.atomic():
            updated = EmailOTP.objects.filter(
                user=user,
                purpose='verification',
                code=code,
                is_used=False,
                expires_at__gt=timezone.now(),
            ).update(is_used=True)

            if updated:
                user.is_verified = True
                user.is_active = True
                user.save()
                del request.session['pending_verification_user_id']
                login(request, user)
                return redirect('dashboard')
            else:
                error = 'Invalid or expired code. Please try again.'

    return render(request, 'dashboard/verify_email.html', {
        'error': error,
        'phone': user.phone,
    })


@ratelimit(key='ip', rate='3/m', method=['GET', 'POST'], block=True)
def resend_otp_view(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    EmailOTP.objects.filter(user=user, purpose='verification', is_used=False).update(is_used=True)

    otp = EmailOTP(user=user, purpose='verification')
    otp.save()
    send_otp_sms(user.phone, otp.code, purpose='verification')

    return redirect('verify-email')


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            user_obj = None

        if user_obj and user_obj.check_password(password):
            if not user_obj.is_verified:
                EmailOTP.objects.filter(user=user_obj, purpose='verification', is_used=False).update(is_used=True)
                otp = EmailOTP(user=user_obj, purpose='verification')
                otp.save()
                send_otp_sms(user_obj.phone, otp.code, purpose='verification')
                request.session['pending_verification_user_id'] = user_obj.id
                return redirect('verify-email')
            else:
                login(request, user_obj)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
        else:
            error = 'Invalid email or password.'

    return render(request, 'dashboard/login.html', {'error': error})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def forgot_password_view(request):
    error = None
    success = None

    if request.method == 'POST':
        country_code = request.POST.get('country_code', '+1').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        phone = normalize_phone(country_code + phone_number)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            user = None

        if user:
            EmailOTP.objects.filter(
                user=user, purpose='password_reset', is_used=False,
            ).update(is_used=True)

            otp = EmailOTP(user=user, purpose='password_reset')
            otp.save()
            send_otp_sms(user.phone, otp.code, purpose='password_reset')

            request.session['password_reset_user_id'] = user.id
            return redirect('reset-password')
        else:
            success = 'If an account with this phone number exists, a reset code has been sent.'

    return render(request, 'dashboard/forgot_password.html', {
        'error': error,
        'success': success,
    })


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def reset_password_view(request):
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        return redirect('forgot-password')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('forgot-password')

    error = None
    if request.method == 'POST':
        code = request.POST.get('otp_code', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password != confirm_password:
            error = 'Passwords do not match.'
        elif len(new_password) < 8:
            error = 'Password must be at least 8 characters.'
        else:
            # Use atomic update to prevent race condition
            with transaction.atomic():
                updated = EmailOTP.objects.filter(
                    user=user,
                    purpose='password_reset',
                    code=code,
                    is_used=False,
                    expires_at__gt=timezone.now(),
                ).update(is_used=True)

                if updated:
                    user.set_password(new_password)
                    user.save()
                    del request.session['password_reset_user_id']
                    return redirect('login')
                else:
                    error = 'Invalid or expired code.'

    return render(request, 'dashboard/reset_password.html', {
        'error': error,
        'phone': user.phone,
    })
