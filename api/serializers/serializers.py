from rest_framework import serializers
from api.models import Driver, Vehicle, Assignment, SMSLog


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
