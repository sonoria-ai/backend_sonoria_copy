from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RegistrationStepAPIView,OrganizationViewSet,ServiceViewSet,OptionViewSet,BusinessHoursViewSet,ExceptionalClosingViewSet,ReservationTypeViewSet,SMSSettingViewSet,GoogleCalendarSettingViewSet,OrganizationFAQViewSet,AssistantViewSet,FallbackNumberViewSet,generate_prompt_view
from .views_dashboard import (
    DashboardOrganizationViewSet, DashboardServiceViewSet, DashboardOptionViewSet,
    ServiceLocationViewSet, BusinessHoursViewSet as DashboardBusinessHoursViewSet,
    ServiceAddOnViewSet, TeamMemberViewSet, BookingRuleViewSet, CommunicationTemplateViewSet,
    FAQViewSet, AssistantViewSet as DashboardAssistantViewSet, FallbackNumberViewSet as DashboardFallbackNumberViewSet
)


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

dashboard_router = DefaultRouter()
dashboard_router.register(r'organization', DashboardOrganizationViewSet, basename='dashboard-organization')
dashboard_router.register(r'service', DashboardServiceViewSet, basename='dashboard-service')
dashboard_router.register(r'option', DashboardOptionViewSet, basename='dashboard-option')
dashboard_router.register(r'service-location', ServiceLocationViewSet, basename='dashboard-service-location')
dashboard_router.register(r'business-hours', DashboardBusinessHoursViewSet, basename='dashboard-business-hours')
dashboard_router.register(r'service-addons', ServiceAddOnViewSet, basename='dashboard-service-addons')
dashboard_router.register(r'team-members', TeamMemberViewSet, basename='dashboard-team-members')
dashboard_router.register(r'booking-rules', BookingRuleViewSet, basename='dashboard-booking-rules')
dashboard_router.register(r'communication-templates', CommunicationTemplateViewSet, basename='dashboard-communication-templates')
dashboard_router.register(r'faqs', FAQViewSet, basename='dashboard-faqs')
dashboard_router.register(r'assistant', DashboardAssistantViewSet, basename='dashboard-assistant')
dashboard_router.register(r'fallback-numbers', DashboardFallbackNumberViewSet, basename='dashboard-fallback-numbers')

urlpatterns = [
    path('registration-steps/', RegistrationStepAPIView.as_view(), name='registration-steps'),
    path('', include(router.urls)),
    path('dashboard/', include(dashboard_router.urls)),
    path('generate-prompt/<int:organization_id>/', generate_prompt_view, name='generate_prompt'),
]
