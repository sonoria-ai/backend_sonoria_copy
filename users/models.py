from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    reset_token = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  

    def __str__(self):
        return self.email

class PaymentPlan(models.Model):
    PLAN_CHOICES = [
        ("Essential", "Essential"),
        ("Advance", "Advance"),
        ("Premium", "Premium"),
    ]
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    monthly_price = models.DecimalField(max_digits=6, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - Monthly: ${self.monthly_price} | Yearly: ${self.yearly_price}"


class UserSubscription(models.Model):
    DURATION_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(PaymentPlan, on_delete=models.SET_NULL, null=True)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default="monthly")
    start_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'} ({self.duration})"



