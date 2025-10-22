import stripe
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, UserSubscription, PaymentPlan

stripe.api_key = settings.STRIPE_SECRET_KEY  # Ensure it's set in settings.py


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    duration = serializers.ChoiceField(choices=UserSubscription.DURATION_CHOICES, write_only=True)
    plan_name = serializers.ChoiceField(choices=[(plan[0], plan[1]) for plan in PaymentPlan.PLAN_CHOICES], write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "plan_name", "duration"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        duration = validated_data.pop("duration")
        plan_name = validated_data.pop("plan_name")
  
        # Check if a user already exists with this email
        if User.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        # Fetch plan based on name
        plan = PaymentPlan.objects.filter(name=plan_name, is_active=True).first()
        if not plan:
            raise serializers.ValidationError({"plan_name": "No active plan found with this name."})

        # Determine price based on duration
        price = plan.monthly_price if duration == "monthly" else plan.yearly_price

        # Create user
        user = User.objects.create(
            email=validated_data["email"],
            password=make_password(password),
            username=validated_data["email"],
        )

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",  # Ensure it's set to subscription mode
            customer_email=user.email,
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"{plan.name} - {duration.capitalize()}"},
                        "recurring": {"interval": "month" if duration == "monthly" else "year"},  # Add this line
                        "unit_amount": int(price * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.FRONTEND_URL}/payment?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/payment-failed",
        )

        # Store Subscription in DB (Initially inactive)
        UserSubscription.objects.create(
            user=user,
            plan=plan,
            duration=duration,
            is_active=False,
        )

        return {"user": user, "payment_url": checkout_session.url}

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("No user with this email found.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=6)

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password"]

    def create(self, validated_data):
        if User.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user