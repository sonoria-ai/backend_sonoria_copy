from django.db import models
from users.models import User


class ServiceLocation(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('one-main', 'Only one main address'),
        ('multiple-locations', 'Multiple locations or rooms'),
        ('client-location', "At client's location"),
    ]

    organization = models.OneToOneField('Organization', on_delete=models.CASCADE, related_name='service_location')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    main_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - {self.get_address_type_display()}"


class Location(models.Model):
    service_location = models.ForeignKey(ServiceLocation, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=255)
    address = models.TextField()
    image = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.service_location.organization.name}"

# Organization Model
class Organization(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organizations")
    # Step 1: Preferences
    use_integrated_booking = models.BooleanField(null=True, blank=True)
    booking_url = models.URLField(max_length=500, blank=True, null=True)
    use_phone_service = models.BooleanField(null=True, blank=True)
    # Step 2: Organization Information
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    business_line = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # Progress tracking
    current_step = models.PositiveIntegerField(default=1)
    assistant_created = models.BooleanField(default=False)

    def __str__(self):
        return self.name if self.name else f"Organization {self.id}"

# Step Tracking Model
class RegistrationStep(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.organization.name} - Step {self.step_number} {'(Completed)' if self.is_completed else '(Pending)'}"

# Step 2: Service Model (Linked to Organization)
class Service(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    detail = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# Step 3: Option Model (Associated with Organization & Service)
class Option(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='options')
    services = models.ManyToManyField(Service, related_name='options', blank=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    detail = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class ServiceAddOnConfig(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='addon_config')
    propose_addons = models.BooleanField(default=False)

    def __str__(self):
        return f"Add-on Config - {self.organization.name}"


class TeamMemberConfig(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='team_config')
    has_multiple_members = models.BooleanField(default=False)
    allow_staff_self_manage = models.BooleanField(default=False)
    allow_client_choose_worker = models.BooleanField(default=False)
    auto_assign_bookings = models.BooleanField(default=False)

    def __str__(self):
        return f"Team Config - {self.organization.name}"


class TeamMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='team_members')
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, related_name='team_members', null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    portfolio_url = models.URLField(blank=True, null=True)
    profile_image = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# Step 2: Business Hours Model (Linked to Organization)
class BusinessHours(models.Model):
    HOURS_TYPE_CHOICES = [
        ('closed', 'Closed'),
        ('open_24', 'Open 24 Hours'),
        ('custom', 'Custom Hours'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='business_hours')
    location = models.ForeignKey('Location', on_delete=models.CASCADE, related_name='business_hours', null=True, blank=True)
    day_of_week = models.CharField(max_length=10)
    hours_type = models.CharField(max_length=10, choices=HOURS_TYPE_CHOICES, default='custom')
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        loc_name = f" - {self.location.name}" if self.location else ""
        return f"{self.organization.name}{loc_name} - {self.day_of_week} ({self.hours_type})"

class OrganizationPrompt(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='prompt')
    generated_prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt for {self.organization.name}"



# Step 3: Exceptional Closings (Temporary Closures & Special Openings)
class ExceptionalClosing(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='exceptional_closings')
    location = models.ForeignKey('Location', on_delete=models.CASCADE, related_name='exceptional_closings', null=True, blank=True)
    open_date = models.DateField()
    close_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        loc_name = f" - {self.location.name}" if self.location else ""
        return f"{self.organization.name}{loc_name} - {self.open_date} to {self.close_date} ({self.reason if self.reason else 'No reason'})"
    
# Step 4: Reservation Type (Linked to Organization)
class ReservationType(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='reservation_types')
    type_choice = models.CharField(
        max_length=50, 
        choices=[('sms', 'SMS'), ('google_calendar', 'Google Calendar')]
    )
    cutoff_time = models.TimeField()
    allow_modifications = models.BooleanField(default=True)
    modification_deadline = models.TimeField(null=True, blank=True)
    allow_cancellations = models.BooleanField(default=True)
    cancellation_deadline = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.organization.name} - {self.type_choice}"


# Step 4: SMS Settings (User Defines SMS Message)
class SMSSetting(models.Model):
    reservation_type = models.OneToOneField(ReservationType, on_delete=models.CASCADE, related_name='sms_settings')
    message_template = models.TextField(help_text="Write the SMS that Gabby will send during the call. Make sure to include your booking link.")

    def __str__(self):
        return f"SMS for {self.reservation_type.organization.name}"


# Step 5: Google Calendar Integration (Now Includes Message Template)
class GoogleCalendarSetting(models.Model):
    reservation_type = models.OneToOneField(ReservationType, on_delete=models.CASCADE, related_name='google_calendar_settings')
    google_calendar_id = models.CharField(max_length=255)
    message_template = models.TextField(help_text="Write the message that will be sent with the Google Calendar invite. Make sure to include your booking link.")

    def __str__(self):
        return f"Google Calendar for {self.reservation_type.organization.name}"
    
# Step 6: Organization FAQ
class OrganizationFAQ(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return f"FAQ - {self.organization.name}"
    
# Step 7: Virtual Assistant
class Assistant(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='assistant')
    name = models.CharField(max_length=255)
    voice_type = models.CharField(max_length=255)
    greeting_message = models.TextField(blank=True, null=True, help_text="First sentence when assistant picks up")
    twilio_phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Dedicated Twilio phone number")
    twilio_phone_sid = models.CharField(max_length=100, blank=True, null=True, help_text="Twilio phone number SID")
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Assistant {self.name} - {self.organization.name}"
    
# Step 8: Fallback Number
class FallbackNumber(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fallback_numbers')
    phone_number = models.CharField(max_length=15)
    reason = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for transferring the call")

    def __str__(self):
        return f"Fallback - {self.organization.name} ({self.reason})"

# Step 7: Booking Rules
class BookingRule(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='booking_rule')

    # Cutoff time settings
    set_cutoff_time = models.BooleanField(default=False)
    cutoff_time_value = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., '15 minutes before', '1 hour before'")

    # Minimum gap between appointments
    set_minimum_gap = models.BooleanField(default=False)
    gap_time_value = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 'No gap', '15 minutes', '1 hour'")

    # Modifications settings
    allow_modifications = models.BooleanField(default=True)
    modifications_deadline = models.CharField(max_length=50, blank=True, null=True, help_text="Deadline before appointment")

    # Cancellations settings
    allow_cancellations = models.BooleanField(default=True)
    cancellation_deadline = models.CharField(max_length=50, blank=True, null=True, help_text="Deadline before appointment")

    # Email reminder
    email_reminder_delay = models.CharField(max_length=50, blank=True, null=True, help_text="When to send reminder before appointment")

    # Newsletter and T&C
    offer_newsletter = models.BooleanField(default=False)
    terms_and_conditions_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Booking Rules - {self.organization.name}"

# Step 8: Communication Templates
class CommunicationTemplate(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='communication_template')

    # Booking SMS (no subject for SMS)
    booking_sms_content = models.TextField(help_text="SMS sent by Gabby to clients with booking link")

    # Confirmation Email
    confirmation_email_subject = models.CharField(max_length=255, default="Your appointment is confirmed ✅")
    confirmation_email_content = models.TextField(help_text="Email sent after booking confirmation")

    # Modification Email
    modification_email_subject = models.CharField(max_length=255, default="Your appointment has been updated ✅")
    modification_email_content = models.TextField(help_text="Email sent after appointment modification")

    # Cancellation Email
    cancellation_email_subject = models.CharField(max_length=255, default="Your appointment has been canceled ❌")
    cancellation_email_content = models.TextField(help_text="Email sent after appointment cancellation")

    # Reminder Email
    reminder_email_subject = models.CharField(max_length=255, default="Reminder - Your appointment is coming up 📅")
    reminder_email_content = models.TextField(help_text="Reminder email sent before appointment")

    def __str__(self):
        return f"Communication Templates - {self.organization.name}"


# Customer Model - matches frontend BookingData and CustomerAccount interfaces
class Customer(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='customers')
    email = models.EmailField()  # Primary identifier
    first_name = models.CharField(max_length=255, blank=True)  # firstName in frontend
    last_name = models.CharField(max_length=255, blank=True)  # lastName in frontend
    phone = models.CharField(max_length=20, blank=True)  # phone in frontend (not phone_number)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'email')
        indexes = [
            models.Index(fields=['organization', 'email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.organization.name}"


# Appointment Model - matches frontend BookingData interface
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')

    # Booking selections - matching frontend BookingData interface
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='appointments', null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='appointments')
    options = models.ManyToManyField(Option, related_name='appointments', blank=True)  # selectedOptions in frontend
    provider = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, related_name='appointments_as_provider', null=True, blank=True)  # called 'provider' in frontend

    # Date and time - matching frontend field names
    date = models.DateField()  # matches 'date' in frontend
    time = models.TimeField()  # matches 'time' in frontend

    # Calculated fields
    duration = models.PositiveIntegerField(help_text="Total duration in minutes (service + options)")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price (service + options)")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Notes - matches 'note' in frontend
    note = models.TextField(blank=True, default='', help_text="Customer notes from booking")
    internal_notes = models.TextField(blank=True, default='', help_text="Internal staff notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['organization', 'date', 'status']),
            models.Index(fields=['customer', '-date']),
        ]

    def __str__(self):
        return f"{self.customer.first_name} {self.customer.last_name} - {self.service.name} on {self.date} at {self.time}"
