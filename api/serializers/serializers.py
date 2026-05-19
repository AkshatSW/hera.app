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

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        instance = getattr(self, 'instance', None)
        driver = attrs.get('driver', getattr(instance, 'driver', None))
        vehicle = attrs.get('vehicle', getattr(instance, 'vehicle', None))

        if driver is not None:
            if user and driver.user_id != user.id:
                raise serializers.ValidationError({'driver': 'Invalid associate for this account.'})
            if driver.status != 'active':
                raise serializers.ValidationError({
                    'driver': 'Inactive associates cannot be assigned to routes.',
                })

        if vehicle is not None:
            if user and vehicle.user_id != user.id:
                raise serializers.ValidationError({'vehicle': 'Invalid vehicle for this account.'})
            if vehicle.status != 'active':
                raise serializers.ValidationError({
                    'vehicle': 'Grounded vehicles cannot be assigned to routes.',
                })

        return attrs


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


class ManualDailyRouteCreateSerializer(serializers.Serializer):
    """Payload for adding a DailyRoute outside of Excel import."""
    route_code = serializers.CharField(max_length=50)
    driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.none(),
        help_text='Active associate PK (must belong to current user)',
    )
    dsp = serializers.CharField(max_length=255, allow_blank=True, required=False, default='')
    transporter_id = serializers.CharField(max_length=100, allow_blank=True, required=False, default='')
    route_date = serializers.DateField(required=False, allow_null=True)
    route_progress = serializers.ChoiceField(
        choices=['not_started', 'in_progress', 'completed'],
        default='not_started',
        required=False,
    )
    delivery_service_type = serializers.ChoiceField(
        choices=['AMZL', 'DSP', 'LINEHAUL'],
        default='DSP',
        required=False,
    )
    route_duration = serializers.CharField(max_length=50, allow_blank=True, required=False, default='')
    all_stops = serializers.IntegerField(min_value=0, default=0, required=False)
    stops_completed = serializers.IntegerField(min_value=0, default=0, required=False)
    not_started_stops = serializers.IntegerField(min_value=0, default=0, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            self.fields['driver'].queryset = Driver.objects.filter(user=user, status='active')


class DailyRouteLinkDriverSerializer(serializers.Serializer):
    """Serializer for manually linking a driver to a DailyRoute."""
    driver_id = serializers.IntegerField()


class DailyRouteBulkSMSSerializer(serializers.Serializer):
    """Serializer for bulk SMS sending."""
    route_ids = serializers.ListField(child=serializers.IntegerField())
