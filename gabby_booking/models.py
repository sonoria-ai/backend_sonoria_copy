from django.db import models
from users.models import User

# Organization Model
class Organization(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organizations")
    name = models.CharField(max_length=255)
    business_line = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    description = models.TextField()
    registration_step = models.PositiveIntegerField(default=1)  # Tracks current step

    def __str__(self):
        return self.name

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
    details = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# Step 3: Option Model (Associated with Organization & Service)
class Option(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='options')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='options', blank=True, null=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name} ({self.service.name if self.service else 'No Service'})"
    

# Step 2: Business Hours Model (Linked to Organization)
class BusinessHours(models.Model):
    HOURS_TYPE_CHOICES = [
        ('closed', 'Closed'),
        ('open_24', 'Open 24 Hours'),
        ('custom', 'Custom Hours'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='business_hours')
    day_of_week = models.CharField(max_length=10)  # Monday to Sunday
    hours_type = models.CharField(max_length=10, choices=HOURS_TYPE_CHOICES, default='custom')
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - {self.day_of_week} ({self.hours_type})"

class OrganizationPrompt(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='prompt')
    generated_prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt for {self.organization.name}"



# Step 3: Exceptional Closings (Temporary Closures & Special Openings)
class ExceptionalClosing(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='exceptional_closings')
    open_date = models.DateField()  # When the business will open
    close_date = models.DateField()  # When the business will close
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - {self.open_date} to {self.close_date} ({self.reason if self.reason else 'No reason'})"
    
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
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='assistants')
    name = models.CharField(max_length=255)
    voice_type = models.CharField(max_length=255)

    def __str__(self):
        return f"Assistant {self.name} - {self.organization.name}"
    
# Step 8: Fallback Number
class FallbackNumber(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fallback_numbers')
    phone_number = models.CharField(max_length=15)
    reason = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for transferring the call")

    def __str__(self):
        return f"Fallback - {self.organization.name} ({self.reason})"
