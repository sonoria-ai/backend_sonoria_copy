"""
Booking Portal API Views
Handles all booking portal endpoints for customer-facing booking functionality
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import logging

from .models import (
    Organization, Customer, Appointment, Service, Option,
    Location, TeamMember, BusinessHours
)
from .serializers import (
    CustomerSerializer, AppointmentSerializer, BookingCreateSerializer,
    BookingPortalLocationSerializer, BookingPortalServiceSerializer,
    BookingPortalProviderSerializer, OrganizationSerializer
)
from .notifications import send_booking_notification

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_organization_booking_details(request, organization_id):
    """
    Get organization details for booking portal
    Returns organization info, locations, services, and team members

    GET /api/booking/organization/<organization_id>/
    """
    try:
        organization = get_object_or_404(Organization, id=organization_id)

        # Get all related booking data
        # Location is linked via ServiceLocation, not directly to Organization
        locations = Location.objects.filter(service_location__organization=organization)
        services = Service.objects.filter(organization=organization)
        team_members = TeamMember.objects.filter(organization=organization)

        # Serialize data
        data = {
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'industry': organization.industry,
                'description': organization.description,
            },
            'locations': BookingPortalLocationSerializer(locations, many=True).data,
            'services': BookingPortalServiceSerializer(services, many=True).data,
            'providers': BookingPortalProviderSerializer(team_members, many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching organization booking details: {str(e)}")
        return Response(
            {'error': 'Failed to fetch organization details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_customer_by_email(request):
    """
    Search for existing customer by email
    Returns customer data if found, null if not found

    GET /api/booking/customer/search/?email=<email>&organization_id=<org_id>
    """
    email = request.GET.get('email', '').strip().lower()
    organization_id = request.GET.get('organization_id')

    if not email or not organization_id:
        return Response(
            {'error': 'Email and organization_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        customer = Customer.objects.filter(
            email=email,
            organization_id=organization_id
        ).first()

        if customer:
            return Response(CustomerSerializer(customer).data, status=status.HTTP_200_OK)
        else:
            return Response({'customer': None}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error searching for customer: {str(e)}")
        return Response(
            {'error': 'Failed to search for customer'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_booking(request):
    """
    Create a new booking/appointment
    Accepts all booking data from frontend and creates customer + appointment

    POST /api/booking/create/
    Request body matches frontend BookingData interface:
    {
        "email": "customer@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+1234567890",
        "organization_id": 1,
        "location_id": 1,
        "service_id": 1,
        "option_ids": [1, 2],
        "provider_id": 1,
        "date": "2025-01-15",
        "time": "9:00 am",
        "note": "Customer notes"
    }
    """
    try:
        serializer = BookingCreateSerializer(data=request.data)

        if serializer.is_valid():
            appointment = serializer.save()

            # Send SMS notification
            try:
                send_booking_notification(appointment, notification_type='created')
                logger.info(f"Booking confirmation SMS sent for appointment {appointment.id}")
            except Exception as sms_error:
                # Log error but don't fail the booking
                logger.error(f"Failed to send booking SMS: {str(sms_error)}")

            # Return full appointment data
            response_data = AppointmentSerializer(appointment).data

            return Response(
                {
                    'success': True,
                    'message': 'Booking created successfully',
                    'appointment': response_data
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    'success': False,
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Failed to create booking',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_time_slots(request):
    """
    Get available time slots for a specific date, service, and provider

    GET /api/booking/time-slots/?organization_id=<org_id>&date=<date>&service_id=<service_id>&provider_id=<provider_id>
    """
    organization_id = request.GET.get('organization_id')
    date = request.GET.get('date')
    service_id = request.GET.get('service_id')
    provider_id = request.GET.get('provider_id')

    if not all([organization_id, date, service_id]):
        return Response(
            {'error': 'organization_id, date, and service_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from datetime import datetime, timedelta

        # Get service to know duration
        service = get_object_or_404(Service, id=service_id)

        # Get business hours for the organization
        business_hours = BusinessHours.objects.filter(
            organization_id=organization_id
        ).first()

        # Get existing appointments for this date and provider
        existing_appointments = Appointment.objects.filter(
            organization_id=organization_id,
            date=date,
            status__in=['pending', 'confirmed']
        )

        if provider_id:
            existing_appointments = existing_appointments.filter(provider_id=provider_id)

        # Generate time slots (simplified - you can make this more sophisticated)
        # For now, generate hourly slots from 9 AM to 6 PM
        time_slots = []
        current_time = datetime.strptime("09:00 AM", "%I:%M %p")
        end_time = datetime.strptime("06:00 PM", "%I:%M %p")

        while current_time <= end_time:
            time_str = current_time.strftime("%I:%M %p").lower().lstrip('0')

            # Check if this time slot is already booked
            is_booked = existing_appointments.filter(
                time=current_time.time()
            ).exists()

            time_slots.append({
                'time': time_str,
                'available': not is_booked
            })

            current_time += timedelta(hours=1)

        return Response({
            'date': date,
            'time_slots': time_slots
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching time slots: {str(e)}")
        return Response(
            {'error': 'Failed to fetch time slots'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_customer_appointments(request):
    """
    Get appointments for a specific customer

    GET /api/booking/customer/appointments/?email=<email>&organization_id=<org_id>
    """
    email = request.GET.get('email', '').strip().lower()
    organization_id = request.GET.get('organization_id')

    if not email or not organization_id:
        return Response(
            {'error': 'Email and organization_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Find customer
        customer = Customer.objects.filter(
            email=email,
            organization_id=organization_id
        ).first()

        if not customer:
            return Response({'appointments': []}, status=status.HTTP_200_OK)

        # Get appointments
        appointments = Appointment.objects.filter(
            customer=customer
        ).order_by('-date', '-time')

        return Response({
            'customer': CustomerSerializer(customer).data,
            'appointments': AppointmentSerializer(appointments, many=True).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching customer appointments: {str(e)}")
        return Response(
            {'error': 'Failed to fetch appointments'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([AllowAny])
def reschedule_appointment(request, appointment_id):
    """
    Reschedule an appointment to a new date and time

    PATCH /api/booking/appointments/<appointment_id>/reschedule/
    Body: { "date": "2025-01-20", "time": "10:00 am" }
    """
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)

        new_date = request.data.get('date')
        new_time = request.data.get('time')

        if not new_date or not new_time:
            return Response(
                {'error': 'Both date and time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store old date/time for SMS notification
        old_date = appointment.date
        old_time = appointment.time

        # Convert 12-hour format to 24-hour format if needed
        from datetime import datetime
        try:
            # Try parsing as 12-hour format first (e.g., "10:00 am")
            time_obj = datetime.strptime(new_time, '%I:%M %p')
            new_time = time_obj.strftime('%H:%M:%S')
        except ValueError:
            # If that fails, try 24-hour format (e.g., "10:00:00")
            try:
                time_obj = datetime.strptime(new_time, '%H:%M:%S')
            except ValueError:
                # Try without seconds (e.g., "10:00")
                try:
                    time_obj = datetime.strptime(new_time, '%H:%M')
                    new_time = time_obj.strftime('%H:%M:%S')
                except ValueError:
                    return Response(
                        {'error': 'Invalid time format. Use "HH:MM am/pm" or "HH:MM:SS"'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Update appointment
        appointment.date = new_date
        appointment.time = new_time
        appointment.save()

        # Send SMS notification
        try:
            send_booking_notification(
                appointment,
                notification_type='rescheduled',
                old_date=old_date,
                old_time=old_time
            )
            logger.info(f"Reschedule SMS sent for appointment {appointment.id}")
        except Exception as sms_error:
            logger.error(f"Failed to send reschedule SMS: {str(sms_error)}")

        return Response({
            'success': True,
            'message': 'Appointment rescheduled successfully',
            'appointment': AppointmentSerializer(appointment).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        return Response(
            {'error': 'Failed to reschedule appointment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([AllowAny])
def cancel_appointment(request, appointment_id):
    """
    Cancel an appointment

    PATCH /api/booking/appointments/<appointment_id>/cancel/
    Body: { "reason": "Scheduling conflict" }
    """
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)

        reason = request.data.get('reason', 'Customer requested cancellation')

        # Update appointment status
        appointment.status = 'cancelled'
        appointment.internal_notes = f"Cancellation reason: {reason}"
        appointment.cancelled_at = timezone.now()
        appointment.save()

        # Send SMS notification
        try:
            send_booking_notification(appointment, notification_type='cancelled')
            logger.info(f"Cancellation SMS sent for appointment {appointment.id}")
        except Exception as sms_error:
            logger.error(f"Failed to send cancellation SMS: {str(sms_error)}")

        return Response({
            'success': True,
            'message': 'Appointment cancelled successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return Response(
            {'error': 'Failed to cancel appointment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
