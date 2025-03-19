from django.shortcuts import render


from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
import stripe
from django.conf import settings
from .models import UserSubscription, User
from .serializers import UserRegistrationSerializer
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from rest_framework.exceptions import ValidationError

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY 

class UserRegistrationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.save()

            return Response(
                {
                    "message": "User registered successfully",
                    "payment_url": result["payment_url"],
                    "registered_at": result["user"].date_joined,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            # Handle validation errors (e.g., email already exists)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )



class PaymentSuccessViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def retrieve(self, request, session_id=None):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer_email = session.customer_email
            user = get_object_or_404(User, email=customer_email)

            # Activate user subscription
            subscription = get_object_or_404(UserSubscription, user=user)
            subscription.is_active = True
            subscription.save()

            return Response(
                {"message": "Payment successful, subscription activated."},
                status=status.HTTP_200_OK,
            )
        except stripe.error.StripeError:
            return Response(
                {"error": "Invalid session or payment failed"},
                status=status.HTTP_400_BAD_REQUEST,
            ) 
        

class SignInViewSet(ViewSet):
    permission_classes = [AllowAny]

    def create(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    

class PasswordResetViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"])
    def request_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data["email"])
            token = default_token_generator.make_token(user)
            user.reset_token = token  # Store the token in DB
            user.save()

            reset_link = f"{settings.FRONTEND_URL}/login?step=resetPassword&token={token}"

            send_mail(
                "Password Reset Request",
                f"Click the link to reset your password: {reset_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Reset link sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def confirm_reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = request.headers.get("Authorization")  # Token should be passed in headers
            user = User.objects.filter(reset_token=token).first()

            if not user:
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data["new_password"])
            user.reset_token = None  # Clear token after reset
            user.save()

            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

