from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.models import HeraUser, Driver, Vehicle, Assignment, SMSLog


@admin.register(HeraUser)
class HeraUserAdmin(UserAdmin):
    model = HeraUser
    list_display = ('email', 'first_name', 'last_name', 'dsp_name', 'is_verified', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'dsp_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'dsp_name')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'status', 'created_at')
    search_fields = ('name', 'phone')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_code', 'plate_number', 'status', 'created_at')
    search_fields = ('vehicle_code', 'plate_number')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'vehicle', 'route_code', 'route_date', 'wave_time', 'sms_status')
    list_filter = ('sms_status', 'route_date')
    search_fields = ('route_code', 'driver__name')


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('driver', 'phone', 'status', 'sent_at', 'delivered_at')
    list_filter = ('status',)
    search_fields = ('phone', 'driver__name')
