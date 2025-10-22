"""
URL Configuration for Booking Portal API
All customer-facing booking endpoints
"""
from django.urls import path
from . import views_booking

urlpatterns = [
    # Organization details for booking portal
    path('organization/<int:organization_id>/', views_booking.get_organization_booking_details, name='booking-organization-details'),

    # Customer search and management
    path('customer/search/', views_booking.search_customer_by_email, name='booking-customer-search'),
    path('customer/appointments/', views_booking.get_customer_appointments, name='booking-customer-appointments'),

    # Booking/Appointment creation
    path('create/', views_booking.create_booking, name='booking-create'),

    # Time slots
    path('time-slots/', views_booking.get_available_time_slots, name='booking-time-slots'),

    # Appointment management
    path('appointments/<int:appointment_id>/reschedule/', views_booking.reschedule_appointment, name='booking-reschedule'),
    path('appointments/<int:appointment_id>/cancel/', views_booking.cancel_appointment, name='booking-cancel'),
]
