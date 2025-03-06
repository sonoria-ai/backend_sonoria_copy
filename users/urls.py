from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationViewSet, PaymentSuccessViewSet, SignInViewSet,PasswordResetViewSet

router = DefaultRouter()
router.register(r"register", UserRegistrationViewSet, basename="register")

sign_in_view = SignInViewSet.as_view({'post': 'create'})

password_reset_view = PasswordResetViewSet.as_view({
    "post": "request_reset"
})
password_confirm_view = PasswordResetViewSet.as_view({
    "post": "confirm_reset"
})


urlpatterns = [
    path("", include(router.urls)),
    path("payment-success/<str:session_id>/", PaymentSuccessViewSet.as_view({"get": "retrieve"}), name="payment_success"),
    path('signin/', sign_in_view, name='signin'),
    path("password-reset/", password_reset_view, name="password-reset"),
    path("password-reset/confirm/", password_confirm_view, name="password-reset-confirm"),
]