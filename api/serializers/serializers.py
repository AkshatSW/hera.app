from rest_framework import serializers
from api.models import Driver, Vehicle, Assignment, SMSLog, ImportBatch, DailyRoute


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        exclude = ['user']


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        exclude = ['user']


class AssignmentSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    driver_phone = serializers.CharField(source='driver.phone', read_only=True)
    vehicle_code_display = serializers.CharField(source='vehicle.vehicle_code', read_only=True)
    plate_number = serializers.CharField(source='vehicle.plate_number', read_only=True)
    dsp_name = serializers.CharField(read_only=True)
    transporter_id = serializers.CharField(read_only=True)
    route_progress = serializers.CharField(read_only=True)
    delivery_service_type = serializers.CharField(read_only=True)
    route_duration = serializers.CharField(read_only=True)
    all_stops = serializers.IntegerField(read_only=True)
    not_started_stops = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assignment
        exclude = ['user']


class SMSLogSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.name', read_only=True)

    class Meta:
        model = SMSLog
        fields = '__all__'


class RosterUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class ManualSMSSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField()
    message = serializers.CharField(max_length=1600)


class ImportBatchSerializer(serializers.ModelSerializer):
    """Serializer for ImportBatch."""
    class Meta:
        model = ImportBatch
        exclude = ['user']


class DailyRouteSerializer(serializers.ModelSerializer):
    """Serializer for DailyRoute."""
    driver_name = serializers.SerializerMethodField()
    driver_phone = serializers.SerializerMethodField()
    match_status_display = serializers.SerializerMethodField()
    sms_status_display = serializers.SerializerMethodField()

    class Meta:
        model = DailyRoute
        exclude = ['user']

    def get_driver_name(self, obj):
        """Return driver name, or None if no driver linked."""
        return obj.driver.name if obj.driver else None

    def get_driver_phone(self, obj):
        """Return driver phone, or None if no driver linked."""
        return obj.driver.phone if obj.driver else None

    def get_match_status_display(self, obj):
        """Return human-readable match status."""
        return dict(obj.MATCH_STATUS_CHOICES).get(obj.match_status, obj.match_status)

    def get_sms_status_display(self, obj):
        """Return human-readable SMS status."""
        return dict(obj.SMS_STATUS_CHOICES).get(obj.sms_status, obj.sms_status)


class DailyRouteLinkDriverSerializer(serializers.Serializer):
    """Serializer for manually linking a driver to a DailyRoute."""
    driver_id = serializers.IntegerField()


class DailyRouteBulkSMSSerializer(serializers.Serializer):
    """Serializer for bulk SMS sending."""
    route_ids = serializers.ListField(child=serializers.IntegerField())
