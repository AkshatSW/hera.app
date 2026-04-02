from django.conf import settings
from django.db import models


class Driver(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drivers',
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    transporter_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    dsp = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=20, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drivers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'transporter_id']),
            models.Index(fields=['user', 'dsp']),
            models.Index(fields=['user', 'phone']),
        ]

    def __str__(self):
        phone_str = f" ({self.phone})" if self.phone else ""
        return f"{self.name}{phone_str}"


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


class ImportBatch(models.Model):
    """Track each Excel upload as a batch."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='import_batches',
    )
    file_name = models.CharField(max_length=255)
    total_rows = models.PositiveIntegerField(default=0)
    matched_rows = models.PositiveIntegerField(default=0)
    unmatched_rows = models.PositiveIntegerField(default=0)
    ambiguous_rows = models.PositiveIntegerField(default=0)
    ready_for_sms_rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'import_batches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Batch {self.id} - {self.file_name}"


class DailyRoute(models.Model):
    """Imported route row, matched to driver, tracked for SMS."""
    MATCH_STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('unmatched', 'Unmatched'),
        ('ambiguous', 'Ambiguous'),
    ]

    SMS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]

    DELIVERY_SERVICE_CHOICES = [
        ('AMZL', 'Amazon Logistics'),
        ('DSP', 'Delivery Service Partner'),
        ('LINEHAUL', 'Linehaul'),
    ]

    ROUTE_PROGRESS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_routes',
    )
    batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name='routes',
    )

    # Raw data from Excel
    route_code = models.CharField(max_length=50)
    dsp = models.CharField(max_length=255, blank=True, null=True)
    transporter_id = models.CharField(max_length=100, blank=True, null=True)
    driver_name_raw = models.CharField(max_length=255)
    route_progress = models.CharField(max_length=20, choices=ROUTE_PROGRESS_CHOICES, default='not_started')
    delivery_service_type = models.CharField(max_length=20, choices=DELIVERY_SERVICE_CHOICES, default='DSP')
    route_duration = models.CharField(max_length=50, blank=True, null=True)
    all_stops = models.PositiveIntegerField(default=0)
    stops_completed = models.PositiveIntegerField(default=0)
    not_started_stops = models.PositiveIntegerField(default=0)

    # Matching and SMS tracking
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_routes',
    )
    match_status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='unmatched', db_index=True)
    match_notes = models.TextField(blank=True, null=True)
    sms_status = models.CharField(max_length=20, choices=SMS_STATUS_CHOICES, default='pending', db_index=True)

    route_date = models.DateField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_routes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'batch']),
            models.Index(fields=['user', 'match_status']),
            models.Index(fields=['user', 'sms_status']),
            models.Index(fields=['user', 'route_date']),
        ]

    def __str__(self):
        return f"{self.route_code} - {self.driver_name_raw}"


class Assignment(models.Model):
    SMS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    DELIVERY_SERVICE_CHOICES = [
        ('AMZL', 'Amazon Logistics'),
        ('DSP', 'Delivery Service Partner'),
        ('LINEHAUL', 'Linehaul'),
    ]

    ROUTE_PROGRESS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
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

    # New fields for updated Excel format
    dsp_name = models.CharField(max_length=255, blank=True, null=True)
    transporter_id = models.CharField(max_length=100, blank=True, null=True)
    route_progress = models.CharField(max_length=20, choices=ROUTE_PROGRESS_CHOICES, default='not_started', db_index=True)
    delivery_service_type = models.CharField(max_length=20, choices=DELIVERY_SERVICE_CHOICES, default='DSP')
    route_duration = models.CharField(max_length=50, blank=True, null=True)
    all_stops = models.PositiveIntegerField(default=0)
    not_started_stops = models.PositiveIntegerField(default=0)

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

    # Legacy support for Assignment
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_logs')

    # New: link to DailyRoute
    daily_route = models.ForeignKey(DailyRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_logs')

    class Meta:
        db_table = 'sms_logs'
        ordering = ['sent_at']

    def __str__(self):
        return f"SMS to {self.phone} - {self.status}"
