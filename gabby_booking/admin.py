from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse  
from django.utils.html import format_html  

from .models import (
    Organization, RegistrationStep, Service, Option, BusinessHours, ExceptionalClosing,
    ReservationType, SMSSetting, GoogleCalendarSetting, OrganizationFAQ, Assistant, FallbackNumber,OrganizationPrompt,
    ServiceLocation, Location, Customer, Appointment
)

### INLINE ADMIN CLASSES ###

class RegistrationStepInline(admin.TabularInline):
    model = RegistrationStep
    extra = 1
    readonly_fields = ('is_completed',)

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    filter_horizontal = ('services',)

class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 1

class ExceptionalClosingInline(admin.TabularInline):
    model = ExceptionalClosing
    extra = 1

class ReservationTypeInline(admin.TabularInline):
    model = ReservationType
    extra = 1

class FAQInline(admin.TabularInline):
    model = OrganizationFAQ
    extra = 1

class AssistantInline(admin.TabularInline):
    model = Assistant
    extra = 1

class FallbackNumberInline(admin.TabularInline):
    model = FallbackNumber
    extra = 1

class SMSSettingInline(admin.StackedInline):
    model = SMSSetting
    extra = 1

class GoogleCalendarSettingInline(admin.StackedInline):
    model = GoogleCalendarSetting
    extra = 1


### ORGANIZATION ADMIN ###

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'business_line', 'industry', 'current_step', 'admin_view_link')
    search_fields = ('name', 'industry', 'business_line', 'owner__email')
    list_filter = ('industry',)
    ordering = ('name',)
    inlines = [
        RegistrationStepInline, ServiceInline, BusinessHoursInline, ExceptionalClosingInline,
        ReservationTypeInline, FAQInline, AssistantInline, FallbackNumberInline
    ]

    def owner(self, obj):
        """Display the owner's email or username."""
        return obj.owner.email if obj.owner else "No Owner"

    owner.admin_order_field = 'owner'
    owner.short_description = "Owner"

    def admin_view_link(self, obj):
            """Provides a direct link to the admin view of this object."""
            return mark_safe(f'<a href="/admin/app_name/organization/{obj.id}/change/">View/Edit</a>')

    admin_view_link.short_description = "Admin Actions" 


### SERVICE ADMIN ###

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'price', 'duration')
    search_fields = ('name', 'organization__name')
    list_filter = ('organization',)


### RESERVATION TYPE ADMIN ###

@admin.register(ReservationType)
class ReservationTypeAdmin(admin.ModelAdmin):
    list_display = ('organization', 'type_choice', 'cutoff_time', 'allow_modifications', 'allow_cancellations')
    list_filter = ('type_choice', 'allow_modifications', 'allow_cancellations')
    search_fields = ('organization__name',)
    inlines = [SMSSettingInline, GoogleCalendarSettingInline]


### OTHER MODELS ADMIN REGISTRATION ###

@admin.register(RegistrationStep)
class RegistrationStepAdmin(admin.ModelAdmin):
    list_display = ('organization', 'step_number', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('organization__name',)

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'price', 'duration')
    search_fields = ('name', 'organization__name')
    list_filter = ('organization',)
    filter_horizontal = ('services',)

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('organization', 'day_of_week', 'hours_type', 'open_time', 'break_start_time', 'break_end_time', 'close_time')
    list_filter = ('organization', 'hours_type')


@admin.register(ExceptionalClosing)
class ExceptionalClosingAdmin(admin.ModelAdmin):
    list_display = ('organization', 'open_date', 'close_date', 'reason')
    list_filter = ('organization',)
    search_fields = ('organization__name', 'reason')

@admin.register(SMSSetting)
class SMSSettingAdmin(admin.ModelAdmin):
    list_display = ('reservation_type', 'get_organization')
    
    def get_organization(self, obj):
        return obj.reservation_type.organization.name
    get_organization.short_description = 'Organization'
    
@admin.register(GoogleCalendarSetting)
class GoogleCalendarSettingAdmin(admin.ModelAdmin):
    list_display = ('reservation_type', 'google_calendar_id', 'get_organization')

    def get_organization(self, obj):
        return obj.reservation_type.organization.name
    get_organization.short_description = 'Organization'

@admin.register(OrganizationFAQ)
class OrganizationFAQAdmin(admin.ModelAdmin):
    list_display = ('organization', 'question', 'answer')
    search_fields = ('organization__name', 'question')

@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ('organization', 'name', 'voice_type')
    search_fields = ('organization__name', 'name')

@admin.register(FallbackNumber)
class FallbackNumberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'phone_number', 'reason')
    search_fields = ('organization__name', 'phone_number')

@admin.register(OrganizationPrompt)
class OrganizationPromptAdmin(admin.ModelAdmin):
    list_display = ('organization', 'created_at')
    search_fields = ('organization__name',)
    ordering = ('-created_at',)


@admin.register(ServiceLocation)
class ServiceLocationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'address_type', 'main_address')
    search_fields = ('organization__name',)
    list_filter = ('address_type',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_organization', 'address')
    search_fields = ('name', 'service_location__organization__name')

    def get_organization(self, obj):
        return obj.service_location.organization.name
    get_organization.short_description = 'Organization'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone', 'get_organization', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'organization__name')
    list_filter = ('organization', 'created_at')
    ordering = ('-created_at',)

    def get_organization(self, obj):
        return obj.organization.name
    get_organization.short_description = 'Organization'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'service', 'date', 'time', 'status', 'total_price', 'get_organization')
    search_fields = ('customer__email', 'customer__first_name', 'customer__last_name', 'service__name')
    list_filter = ('status', 'organization', 'date')
    ordering = ('-date', '-time')
    filter_horizontal = ('options',)
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at')

    fieldsets = (
        ('Booking Information', {
            'fields': ('organization', 'customer', 'status')
        }),
        ('Service Details', {
            'fields': ('service', 'options', 'location', 'provider')
        }),
        ('Date & Time', {
            'fields': ('date', 'time', 'duration')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Notes', {
            'fields': ('note', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

    def get_organization(self, obj):
        return obj.organization.name
    get_organization.short_description = 'Organization'