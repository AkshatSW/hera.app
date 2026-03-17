from django.conf import settings
from django.db import models


class Driver(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drivers',
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    status = models.CharField(max_length=20, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drivers'
        ordering = ['name']
        unique_together = [('user', 'phone')]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Vehicle(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles',
    )
    vehicle_code = models.CharField(max_length=50)
    plate_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicles'
        ordering = ['vehicle_code']
        unique_together = [('user', 'vehicle_code')]

    def __str__(self):
        return f"{self.vehicle_code} ({self.plate_number})"


class Assignment(models.Model):
    SMS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments_owned',
    )
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignments')
    route_code = models.CharField(max_length=50)
    staging = models.CharField(max_length=50)
    pad = models.CharField(max_length=10)
    wave_time = models.TimeField()
    route_date = models.DateField(db_index=True)
    sms_status = models.CharField(max_length=20, choices=SMS_STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assignments'
        ordering = ['-route_date', 'wave_time']
        indexes = [
            models.Index(fields=['user', 'route_date']),
            models.Index(fields=['user', 'sms_status']),
        ]

    def __str__(self):
        return f"{self.driver.name} - {self.route_code} on {self.route_date}"


class SMSLog(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='sms_logs')
    phone = models.CharField(max_length=30)
    message = models.TextField()
    provider_message_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued', db_index=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_logs')

    class Meta:
        db_table = 'sms_logs'
        ordering = ['sent_at']

    def __str__(self):
        return f"SMS to {self.phone} - {self.status}"
