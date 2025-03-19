import logging
from rest_framework import serializers
from .models import RegistrationStep,Organization, Option ,Service,BusinessHours,ExceptionalClosing,ReservationType,SMSSetting, GoogleCalendarSetting,OrganizationFAQ,Assistant,FallbackNumber

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