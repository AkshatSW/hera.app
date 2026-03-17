import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ('verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(
        'api.HeraUser',
        on_delete=models.CASCADE,
        related_name='otps',
    )
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
            models.Index(fields=['code', 'is_used']),
        ]

    def __str__(self):
        return f"OTP {self.code} for {self.user.email} ({self.purpose})"

    def save(self, *args, **kwargs):
        if not self.code:
            # Use cryptographically secure random number generation
            self.code = f"{secrets.randbelow(1000000):06d}"
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
