from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RegistrationStepAPIView,OrganizationViewSet,ServiceViewSet,OptionViewSet,BusinessHoursViewSet,ExceptionalClosingViewSet,ReservationTypeViewSet,SMSSettingViewSet,GoogleCalendarSettingViewSet,OrganizationFAQViewSet,AssistantViewSet,FallbackNumberViewSet,generate_prompt_view

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'options', OptionViewSet, basename='option')
router.register(r'business-hours', BusinessHoursViewSet, basename='business-hours')
router.register(r'exceptional-closings', ExceptionalClosingViewSet, basename='exceptional-closing')
router.register(r'reservation-types', ReservationTypeViewSet, basename='reservation-type')
router.register(r'sms-settings', SMSSettingViewSet, basename='sms-setting')
router.register(r'google-calendar-settings', GoogleCalendarSettingViewSet, basename='google-calendar-setting')
router.register(r'organization-faqs', OrganizationFAQViewSet, basename='organization-faq')
router.register(r'assist-add', AssistantViewSet, basename='assist-add')
router.register(r'fallback-numbers', FallbackNumberViewSet, basename='fallback-number')

urlpatterns = [
    path('registration-steps/', RegistrationStepAPIView.as_view(), name='registration-steps'),
    path('', include(router.urls)),
    path('generate-prompt/<int:organization_id>/', generate_prompt_view, name='generate_prompt')
]
