import logging
from rest_framework import serializers
from .models import (
    RegistrationStep, Organization, Option, Service, BusinessHours, ExceptionalClosing,
    ReservationType, SMSSetting, GoogleCalendarSetting, OrganizationFAQ, Assistant,
    FallbackNumber, OrganizationPrompt, ServiceLocation, Location,
    ServiceAddOnConfig, TeamMemberConfig, TeamMember, BookingRule, CommunicationTemplate,
    Customer, Appointment
)

logger = logging.getLogger(__name__)

class RegistrationStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationStep
        fields = "__all__"

    def validate_step_number(self, value):
        if value < 1:
            logger.warning(f"Invalid step number: {value}")
            raise serializers.ValidationError("Step number must be greater than 0.")
        return value

class OrganizationPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPrompt
        fields = '__all__'

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'  # Include all fields

    def validate_name(self, value):
        """Ensure the name is at least 3 characters long."""
        if len(value) < 3:
            logger.warning("Validation error: Organization name too short")
            raise serializers.ValidationError("Organization name must be at least 3 characters long.")
        return value

    def validate_business_line(self, value):
        """Ensure business line is not empty."""
        if not value.strip():
            logger.warning("Validation error: Business line is empty")
            raise serializers.ValidationError("Business line cannot be empty.")
        return value
    

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

    def validate_price(self, value):
        if value < 0:
            logger.warning("Service price cannot be negative.")
            raise serializers.ValidationError("Price must be a positive value.")
        return value

    def validate_duration(self, value):
        if value <= 0:
            logger.warning("Service duration must be greater than zero.")
            raise serializers.ValidationError("Duration must be greater than zero.")
        return value

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'

    def validate_price(self, value):
        if value < 0:
            logger.warning("Option price cannot be negative.")
            raise serializers.ValidationError("Price must be a positive value.")
        return value

    def validate_duration(self, value):
        if value <= 0:
            logger.warning("Option duration must be greater than zero.")
            raise serializers.ValidationError("Duration must be greater than zero.")
        return value

class BusinessHoursSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(source='location.id', read_only=True, allow_null=True)

    class Meta:
        model = BusinessHours
        fields = '__all__'

    def validate(self, data):
        hours_type = data.get('hours_type')

        if hours_type == 'closed':
            if data.get('open_time') or data.get('close_time'):
                logger.warning("Closed business hours should not have open or close time.")
                raise serializers.ValidationError("Closed business hours should not have open or close time.")
        
        elif hours_type == 'open_24':
            if data.get('open_time') or data.get('close_time'):
                logger.warning("24-hour businesses should not have open or close times.")
                raise serializers.ValidationError("24-hour businesses should not have open or close times.")
        
        elif hours_type == 'custom':
            open_time = data.get('open_time')
            close_time = data.get('close_time')
            if not open_time or not close_time:
                logger.warning("Custom hours require both open and close time.")
                raise serializers.ValidationError("Custom hours require both open and close time.")
            if open_time >= close_time:
                logger.warning("Open time must be earlier than close time.")
                raise serializers.ValidationError("Open time must be earlier than close time.")
        
        return data

class ExceptionalClosingSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(source='location.id', read_only=True, allow_null=True)

    class Meta:
        model = ExceptionalClosing
        fields = '__all__'

    def validate(self, data):
        open_date = data.get('open_date')
        close_date = data.get('close_date')

        if open_date > close_date:
            logger.warning("Open date cannot be after close date.")
            raise serializers.ValidationError("Open date cannot be after close date.")
        
        return data
    
class ReservationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationType
        fields = '__all__'

    def validate(self, data):
        """
        Custom validation to ensure that modification and cancellation deadlines are properly set
        if modifications or cancellations are allowed.
        """
        if data.get('allow_modifications') and not data.get('modification_deadline'):
            logger.warning("Modification deadline required when modifications are allowed.")
            raise serializers.ValidationError("Modification deadline is required when modifications are allowed.")

        if data.get('allow_cancellations') and not data.get('cancellation_deadline'):
            logger.warning("Cancellation deadline required when cancellations are allowed.")
            raise serializers.ValidationError("Cancellation deadline is required when cancellations are allowed.")

        return data


class SMSSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSSetting
        fields = '__all__'

    def validate_message_template(self, value):
        """
        Ensure the SMS message contains a booking link.
        """
        if "booking" not in value.lower():
            logger.warning("SMS message template does not contain a booking link.")
            raise serializers.ValidationError("The message must include a booking link.")
        return value


class GoogleCalendarSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleCalendarSetting
        fields = '__all__'

    def validate_message_template(self, value):
        """
        Ensure the Google Calendar message contains a booking link.
        """
        if "booking" not in value.lower():
            logger.warning("Google Calendar message template does not contain a booking link.")
            raise serializers.ValidationError("The message must include a booking link.")
        return value
    
class OrganizationFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationFAQ
        fields = '__all__'

    def validate_question(self, value):
        """
        Ensure the question is meaningful and not just a generic phrase.
        """
        if len(value.strip()) < 5:
            logger.warning("Validation failed: Question is too short.")
            raise serializers.ValidationError("The question must be at least 5 characters long.")
        return value

    def validate_answer(self, value):
        """
        Ensure the answer is not empty.
        """
        if len(value.strip()) == 0:
            logger.warning("Validation failed: Answer cannot be empty.")
            raise serializers.ValidationError("The answer cannot be empty.")
        return value
    

class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = '__all__'

    def validate_name(self, value):
        if len(value.strip()) < 3:
            logger.warning("Validation failed: Assistant name too short.")
            raise serializers.ValidationError("Assistant name must be at least 3 characters long.")
        return value


class FallbackNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FallbackNumber
        fields = '__all__'

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) < 10:
            logger.warning("Validation failed: Invalid phone number.")
            raise serializers.ValidationError("Enter a valid phone number with at least 10 digits.")
        return value


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'image']


class ServiceLocationSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceLocation
        fields = ['id', 'organization', 'address_type', 'main_address', 'locations']


class ServiceAddOnConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAddOnConfig
        fields = '__all__'


class TeamMemberConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMemberConfig
        fields = '__all__'


class TeamMemberSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(source='location.id', read_only=True, allow_null=True)

    class Meta:
        model = TeamMember
        fields = '__all__'

    def validate_email(self, value):
        if not value or '@' not in value:
            logger.warning("Invalid email address.")
            raise serializers.ValidationError("Enter a valid email address.")
        return value


class BookingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRule
        fields = '__all__'

    def validate(self, data):
        if data.get('set_cutoff_time') and not data.get('cutoff_time_value'):
            logger.warning("Cutoff time value required when cutoff time is enabled.")
            raise serializers.ValidationError("Cutoff time value is required when cutoff time is enabled.")

        if data.get('set_minimum_gap') and not data.get('gap_time_value'):
            logger.warning("Gap time value required when minimum gap is enabled.")
            raise serializers.ValidationError("Gap time value is required when minimum gap is enabled.")

        if data.get('allow_modifications') and not data.get('modifications_deadline'):
            logger.warning("Modifications deadline required when modifications are allowed.")
            raise serializers.ValidationError("Modifications deadline is required when modifications are allowed.")

        if data.get('allow_cancellations') and not data.get('cancellation_deadline'):
            logger.warning("Cancellation deadline required when cancellations are allowed.")
            raise serializers.ValidationError("Cancellation deadline is required when cancellations are allowed.")

        return data


class CommunicationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationTemplate
        fields = '__all__'

    def validate_booking_sms_content(self, value):
        if '{{booking_link}}' not in value:
            logger.warning("Booking SMS must contain {{booking_link}} variable.")
            raise serializers.ValidationError("Booking SMS must contain {{booking_link}} variable.")
        return value


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model - matches frontend CustomerAccount interface"""
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ['id', 'organization', 'email', 'firstName', 'lastName', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        if not value or '@' not in value:
            logger.warning("Invalid email address.")
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def to_representation(self, instance):
        """Return data matching frontend CustomerAccount interface"""
        return {
            'email': instance.email,
            'firstName': instance.first_name,
            'lastName': instance.last_name,
            'phone': instance.phone
        }


class BookingPortalLocationSerializer(serializers.ModelSerializer):
    """Simplified Location serializer for booking portal - matches frontend Location interface"""
    address = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'image']

    def get_address(self, obj):
        # Combine address fields for frontend
        return obj.address if hasattr(obj, 'address') else f"{obj.city}, {obj.state}"


class BookingPortalServiceSerializer(serializers.ModelSerializer):
    """Service serializer for booking portal - matches frontend Service interface"""
    options = OptionSerializer(many=True, read_only=True)
    description = serializers.CharField(source='detail', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'duration', 'price', 'description', 'options']


class BookingPortalProviderSerializer(serializers.ModelSerializer):
    """Team member serializer for booking portal - matches frontend Provider interface"""
    image = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'image']

    def get_image(self, obj):
        # Return a default image or actual image URL if exists
        # Use ui-avatars.com which generates avatar images from names
        if hasattr(obj, 'image') and obj.image:
            return obj.image
        # Generate avatar from name
        name = getattr(obj, 'name', 'Provider')
        return f'https://ui-avatars.com/api/?name={name.replace(" ", "+")}&size=150&background=4F46E5&color=fff'


class AppointmentSerializer(serializers.ModelSerializer):
    """Full Appointment serializer with nested relationships"""
    customer = CustomerSerializer(read_only=True)
    service = BookingPortalServiceSerializer(read_only=True)
    options = OptionSerializer(many=True, read_only=True)
    provider = BookingPortalProviderSerializer(read_only=True)
    location = BookingPortalLocationSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'organization', 'customer', 'location', 'service', 'options', 'provider',
                  'date', 'time', 'duration', 'total_price', 'status', 'note', 'internal_notes',
                  'created_at', 'updated_at', 'confirmed_at', 'cancelled_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at', 'cancelled_at']


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for creating appointments from booking portal - matches frontend BookingData"""
    # Customer information - matches frontend form fields
    email = serializers.EmailField()
    firstName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    lastName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Booking selections - matches frontend BookingData
    organization_id = serializers.IntegerField()
    location_id = serializers.IntegerField(required=False, allow_null=True)
    service_id = serializers.IntegerField()
    option_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        default=list
    )
    provider_id = serializers.IntegerField(required=False, allow_null=True)  # provider not team_member

    # Date and time - matches frontend field names
    date = serializers.DateField()
    time = serializers.CharField(max_length=20)  # Frontend sends as "9:00 am" string

    # Note - matches frontend field name
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_email(self, value):
        if not value or '@' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower()

    def validate_time(self, value):
        """Convert frontend time format (e.g., "9:00 am") to TimeField format"""
        import datetime
        try:
            # Parse time string like "9:00 am" to time object
            time_obj = datetime.datetime.strptime(value.strip(), "%I:%M %p").time()
            return time_obj
        except ValueError:
            raise serializers.ValidationError("Invalid time format. Expected format: '9:00 am'")

    def validate(self, data):
        from django.utils import timezone

        # Validate date is not in the past
        if data['date'] < timezone.now().date():
            raise serializers.ValidationError({"date": "Appointment date cannot be in the past."})

        return data

    def create(self, validated_data):
        from decimal import Decimal

        # Extract organization and related data
        organization_id = validated_data.pop('organization_id')
        service_id = validated_data.pop('service_id')
        option_ids = validated_data.pop('option_ids', [])
        location_id = validated_data.pop('location_id', None)
        provider_id = validated_data.pop('provider_id', None)

        # Extract customer data
        email = validated_data.pop('email')
        first_name = validated_data.pop('firstName', '')
        last_name = validated_data.pop('lastName', '')
        phone = validated_data.pop('phone', '')

        # Get or create customer
        organization = Organization.objects.get(id=organization_id)
        customer, created = Customer.objects.get_or_create(
            organization=organization,
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone
            }
        )

        # Update customer info if already exists
        if not created:
            customer.first_name = first_name or customer.first_name
            customer.last_name = last_name or customer.last_name
            customer.phone = phone or customer.phone
            customer.save()

        # Get service and calculate duration and price
        service = Service.objects.get(id=service_id)
        options = Option.objects.filter(id__in=option_ids)

        total_duration = service.duration + sum(opt.duration for opt in options)
        total_price = service.price + sum(opt.price for opt in options)

        # Create appointment
        appointment = Appointment.objects.create(
            organization=organization,
            customer=customer,
            service=service,
            location_id=location_id,
            provider_id=provider_id,
            date=validated_data['date'],
            time=validated_data['time'],
            duration=total_duration,
            total_price=total_price,
            note=validated_data.get('note', ''),
            status='pending'
        )

        # Add options
        if options:
            appointment.options.set(options)

        return appointment