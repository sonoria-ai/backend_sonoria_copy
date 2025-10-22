import logging
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import (
    Organization, Service, Option, ServiceLocation, Location,
    BusinessHours, ExceptionalClosing, ServiceAddOnConfig, TeamMemberConfig, TeamMember,
    BookingRule, CommunicationTemplate, OrganizationFAQ, Assistant, FallbackNumber
)
from .serializers import (
    OrganizationSerializer,
    ServiceSerializer,
    OptionSerializer,
    ServiceLocationSerializer,
    LocationSerializer,
    BusinessHoursSerializer,
    ExceptionalClosingSerializer,
    ServiceAddOnConfigSerializer,
    TeamMemberConfigSerializer,
    TeamMemberSerializer,
    BookingRuleSerializer,
    CommunicationTemplateSerializer,
    OrganizationFAQSerializer,
    AssistantSerializer,
    FallbackNumberSerializer
)

logger = logging.getLogger(__name__)


class DashboardOrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get', 'post'])
    def current(self, request):
        """Get or create current organization for logged-in user"""
        if request.method == 'GET':
            try:
                # Get the user's organization
                if request.user.is_authenticated:
                    organization = Organization.objects.filter(owner=request.user).first()
                else:
                    # For development without auth
                    organization = Organization.objects.first()

                if organization:
                    serializer = self.get_serializer(organization)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(None, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error fetching current organization: {str(e)}", exc_info=True)
                return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == 'POST':
            # Create new organization for user (happens on step 1 - preferences)
            try:
                if request.user.is_authenticated:
                    owner = request.user
                else:
                    # For development, use first user or create one
                    from users.models import User
                    owner = User.objects.first()
                    if not owner:
                        owner = User.objects.create_user(
                            username='defaultuser',
                            email='default@example.com',
                            password='defaultpass123'
                        )

                organization = Organization.objects.create(
                    owner=owner,
                    current_step=1
                )

                serializer = self.get_serializer(organization)
                logger.info(f"Organization created with ID: {organization.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating organization: {str(e)}", exc_info=True)
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def update_preferences(self, request, pk=None):
        """Step 1: Update preferences"""
        try:
            organization = self.get_object()

            organization.use_integrated_booking = request.data.get('use_integrated_booking')
            organization.booking_url = request.data.get('booking_url', '')
            organization.use_phone_service = request.data.get('use_phone_service')
            organization.current_step = max(organization.current_step, 2)
            organization.save()

            serializer = self.get_serializer(organization)
            return Response({
                'message': 'Preferences saved',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def update_organization(self, request, pk=None):
        """Step 2: Update organization information"""
        try:
            organization = self.get_object()
            data = request.data

            organization.first_name = data.get('first_name', organization.first_name)
            organization.last_name = data.get('last_name', organization.last_name)
            organization.name = data.get('business_name', organization.name)
            organization.industry = data.get('industry', organization.industry)
            organization.description = data.get('business_description', organization.description)
            organization.current_step = max(organization.current_step, 3)
            organization.save()

            serializer = self.get_serializer(organization)
            return Response({
                'message': 'Organization information saved',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating organization: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        try:
            organization = self.get_object()
            services = Service.objects.filter(organization=organization)
            options = Option.objects.filter(organization=organization)

            service_serializer = ServiceSerializer(services, many=True)
            option_serializer = OptionSerializer(options, many=True)

            return Response({
                'services': service_serializer.data,
                'options': option_serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching services: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def complete_services(self, request, pk=None):
        """Complete Services Setup"""
        try:
            organization = self.get_object()
            organization.current_step = max(organization.current_step, 6)
            organization.save()

            return Response({
                'message': 'Services setup completed',
                'current_step': organization.current_step
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error completing services setup: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                service = serializer.save()
                logger.info(f"Service created: {service.name}")
                return Response({
                    'message': 'Service created',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating service: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            service = self.get_object()
            serializer = self.get_serializer(service, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Service updated',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating service: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            service = self.get_object()
            service.delete()
            return Response({'message': 'Service deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting service: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DashboardOptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

    def create(self, request):
        try:
            data = request.data.copy()
            service_ids = data.pop('service_ids', [])

            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                option = serializer.save()

                if service_ids:
                    services = Service.objects.filter(id__in=service_ids)
                    option.services.set(services)

                response_data = serializer.data
                response_data['service_ids'] = list(option.services.values_list('id', flat=True))

                logger.info(f"Option created: {option.name}")
                return Response({
                    'message': 'Option created',
                    'data': response_data
                }, status=status.HTTP_201_CREATED)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating option: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        try:
            option = self.get_object()
            data = request.data.copy()
            service_ids = data.pop('service_ids', None)

            serializer = self.get_serializer(option, data=data, partial=True)
            if serializer.is_valid():
                option = serializer.save()

                if service_ids is not None:
                    services = Service.objects.filter(id__in=service_ids)
                    option.services.set(services)

                response_data = serializer.data
                response_data['service_ids'] = list(option.services.values_list('id', flat=True))

                return Response({
                    'message': 'Option updated',
                    'data': response_data
                }, status=status.HTTP_200_OK)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating option: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            option = self.get_object()
            option.delete()
            return Response({'message': 'Option deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting option: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ServiceLocationViewSet(viewsets.ModelViewSet):
    queryset = ServiceLocation.objects.all()
    serializer_class = ServiceLocationSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_location = ServiceLocation.objects.filter(organization_id=organization_id).first()
            if service_location:
                serializer = self.get_serializer(service_location)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'data': None}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching service location: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_location(self, request):
        try:
            organization_id = request.data.get('organization_id')
            address_type = request.data.get('address_type')
            main_address = request.data.get('main_address', '')
            locations_data = request.data.get('locations', [])

            with transaction.atomic():
                service_location, created = ServiceLocation.objects.update_or_create(
                    organization_id=organization_id,
                    defaults={
                        'address_type': address_type,
                        'main_address': main_address
                    }
                )

                Location.objects.filter(service_location=service_location).delete()

                for location_data in locations_data:
                    Location.objects.create(
                        service_location=service_location,
                        name=location_data.get('name'),
                        address=location_data.get('address'),
                        image=location_data.get('image', '')
                    )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 4)
                organization.save()

                serializer = self.get_serializer(service_location)
                return Response({
                    'message': 'Service location saved',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving service location: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessHoursViewSet(viewsets.ModelViewSet):
    queryset = BusinessHours.objects.all()
    serializer_class = BusinessHoursSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_location = ServiceLocation.objects.filter(organization_id=organization_id).first()
            locations = []
            if service_location and service_location.address_type == 'multiple-locations':
                locations = list(Location.objects.filter(service_location=service_location).values('id', 'name'))

            business_hours = BusinessHours.objects.filter(organization_id=organization_id)
            exceptional_closings = ExceptionalClosing.objects.filter(organization_id=organization_id)

            hours_serializer = BusinessHoursSerializer(business_hours, many=True)
            closings_serializer = ExceptionalClosingSerializer(exceptional_closings, many=True)

            return Response({
                'locations': locations,
                'business_hours': hours_serializer.data,
                'exceptional_closings': closings_serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching business hours: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_hours(self, request):
        try:
            organization_id = request.data.get('organization_id')
            business_hours_data = request.data.get('business_hours', [])
            exceptional_closings_data = request.data.get('exceptional_closings', [])

            with transaction.atomic():
                BusinessHours.objects.filter(organization_id=organization_id).delete()

                for hour_data in business_hours_data:
                    location_id = hour_data.get('location_id')
                    BusinessHours.objects.create(
                        organization_id=organization_id,
                        location_id=location_id if location_id else None,
                        day_of_week=hour_data.get('day_of_week'),
                        hours_type=hour_data.get('hours_type'),
                        open_time=hour_data.get('open_time'),
                        close_time=hour_data.get('close_time'),
                        break_start_time=hour_data.get('break_start_time'),
                        break_end_time=hour_data.get('break_end_time')
                    )

                ExceptionalClosing.objects.filter(organization_id=organization_id).delete()

                for closing_data in exceptional_closings_data:
                    location_id = closing_data.get('location_id')
                    ExceptionalClosing.objects.create(
                        organization_id=organization_id,
                        location_id=location_id if location_id else None,
                        open_date=closing_data.get('open_date'),
                        close_date=closing_data.get('close_date'),
                        reason=closing_data.get('reason', '')
                    )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 5)
                organization.save()

                return Response({
                    'message': 'Business hours saved',
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving business hours: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceAddOnViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            config = ServiceAddOnConfig.objects.filter(organization_id=organization_id).first()
            addons = Option.objects.filter(organization_id=organization_id)
            services = Service.objects.filter(organization_id=organization_id).values('id', 'name')

            config_serializer = ServiceAddOnConfigSerializer(config) if config else None
            addons_serializer = OptionSerializer(addons, many=True)

            return Response({
                'config': config_serializer.data if config_serializer else {'propose_addons': False},
                'addons': addons_serializer.data,
                'services': list(services)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching add-ons: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_config(self, request):
        try:
            organization_id = request.data.get('organization_id')
            propose_addons = request.data.get('propose_addons', False)
            addons_data = request.data.get('addons', [])

            with transaction.atomic():
                config, created = ServiceAddOnConfig.objects.update_or_create(
                    organization_id=organization_id,
                    defaults={'propose_addons': propose_addons}
                )

                if not propose_addons:
                    Option.objects.filter(organization_id=organization_id).delete()
                else:
                    existing_ids = [a.get('id') for a in addons_data if a.get('id')]
                    Option.objects.filter(organization_id=organization_id).exclude(id__in=existing_ids).delete()

                    for addon_data in addons_data:
                        addon_id = addon_data.get('id')
                        service_ids = addon_data.pop('service_ids', [])

                        if addon_id:
                            try:
                                addon = Option.objects.get(id=addon_id, organization_id=organization_id)
                                for key, value in addon_data.items():
                                    if key != 'id':
                                        setattr(addon, key, value)
                                addon.save()
                            except Option.DoesNotExist:
                                addon = Option.objects.create(
                                    organization_id=organization_id,
                                    name=addon_data.get('name'),
                                    price=addon_data.get('price'),
                                    duration=addon_data.get('duration'),
                                    detail=addon_data.get('detail', '')
                                )
                        else:
                            addon = Option.objects.create(
                                organization_id=organization_id,
                                name=addon_data.get('name'),
                                price=addon_data.get('price'),
                                duration=addon_data.get('duration'),
                                detail=addon_data.get('detail', '')
                            )

                        if service_ids:
                            services = Service.objects.filter(id__in=service_ids)
                            addon.services.set(services)

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 7)
                organization.save()

                return Response({
                    'message': 'Add-ons configuration saved',
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving add-ons: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            config = TeamMemberConfig.objects.filter(organization_id=organization_id).first()
            members = TeamMember.objects.filter(organization_id=organization_id)

            service_location = ServiceLocation.objects.filter(organization_id=organization_id).first()
            locations = []
            if service_location:
                locations = list(Location.objects.filter(service_location=service_location).values('id', 'name'))

            config_serializer = TeamMemberConfigSerializer(config) if config else None
            members_serializer = TeamMemberSerializer(members, many=True)

            return Response({
                'config': config_serializer.data if config_serializer else {
                    'has_multiple_members': False,
                    'allow_staff_self_manage': False,
                    'allow_client_choose_worker': False,
                    'auto_assign_bookings': False
                },
                'members': members_serializer.data,
                'locations': locations
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching team members: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_config(self, request):
        try:
            organization_id = request.data.get('organization_id')
            config_data = request.data.get('config', {})
            members_data = request.data.get('members', [])

            with transaction.atomic():
                config, created = TeamMemberConfig.objects.update_or_create(
                    organization_id=organization_id,
                    defaults={
                        'has_multiple_members': config_data.get('has_multiple_members', False),
                        'allow_staff_self_manage': config_data.get('allow_staff_self_manage', False),
                        'allow_client_choose_worker': config_data.get('allow_client_choose_worker', False),
                        'auto_assign_bookings': config_data.get('auto_assign_bookings', False)
                    }
                )

                if not config.has_multiple_members:
                    TeamMember.objects.filter(organization_id=organization_id).delete()
                else:
                    existing_ids = [m.get('id') for m in members_data if m.get('id')]
                    TeamMember.objects.filter(organization_id=organization_id).exclude(id__in=existing_ids).delete()

                    for member_data in members_data:
                        member_id = member_data.get('id')
                        location_id = member_data.get('location_id')

                        if member_id:
                            try:
                                member = TeamMember.objects.get(id=member_id, organization_id=organization_id)
                                member.name = member_data.get('name', member.name)
                                member.email = member_data.get('email', member.email)
                                member.portfolio_url = member_data.get('portfolio_url', member.portfolio_url)
                                member.profile_image = member_data.get('profile_image', member.profile_image)
                                member.location_id = location_id if location_id else None
                                member.save()
                            except TeamMember.DoesNotExist:
                                TeamMember.objects.create(
                                    organization_id=organization_id,
                                    location_id=location_id if location_id else None,
                                    name=member_data.get('name'),
                                    email=member_data.get('email'),
                                    portfolio_url=member_data.get('portfolio_url', ''),
                                    profile_image=member_data.get('profile_image', '')
                                )
                        else:
                            TeamMember.objects.create(
                                organization_id=organization_id,
                                location_id=location_id if location_id else None,
                                name=member_data.get('name'),
                                email=member_data.get('email'),
                                portfolio_url=member_data.get('portfolio_url', ''),
                                profile_image=member_data.get('profile_image', '')
                            )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 8)
                organization.save()

                return Response({
                    'message': 'Team members configuration saved',
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving team members: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookingRuleViewSet(viewsets.ModelViewSet):
    queryset = BookingRule.objects.all()
    serializer_class = BookingRuleSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking_rule = BookingRule.objects.filter(organization_id=organization_id).first()
            if booking_rule:
                serializer = self.get_serializer(booking_rule)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'data': None}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching booking rules: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_rules(self, request):
        try:
            organization_id = request.data.get('organization_id')
            rules_data = {
                'set_cutoff_time': request.data.get('set_cutoff_time', False),
                'cutoff_time_value': request.data.get('cutoff_time_value', ''),
                'set_minimum_gap': request.data.get('set_minimum_gap', False),
                'gap_time_value': request.data.get('gap_time_value', ''),
                'allow_modifications': request.data.get('allow_modifications', True),
                'modifications_deadline': request.data.get('modifications_deadline', ''),
                'allow_cancellations': request.data.get('allow_cancellations', True),
                'cancellation_deadline': request.data.get('cancellation_deadline', ''),
                'email_reminder_delay': request.data.get('email_reminder_delay', ''),
                'offer_newsletter': request.data.get('offer_newsletter', False),
                'terms_and_conditions_url': request.data.get('terms_and_conditions_url', ''),
            }

            with transaction.atomic():
                booking_rule, created = BookingRule.objects.update_or_create(
                    organization_id=organization_id,
                    defaults=rules_data
                )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 9)
                organization.save()

                serializer = self.get_serializer(booking_rule)
                return Response({
                    'message': 'Booking rules saved',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving booking rules: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    queryset = CommunicationTemplate.objects.all()
    serializer_class = CommunicationTemplateSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = CommunicationTemplate.objects.filter(organization_id=organization_id).first()
            if template:
                serializer = self.get_serializer(template)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)

            # Return default templates if none exist
            default_template = {
                'booking_sms_content': '''Hi this is {{assistant_name}} from {{business_name}}.

Here's the link to book your appointment easily :

{{booking_link}}

Let me know if you need anything, I'm happy to help.''',
                'confirmation_email_subject': 'Your appointment is confirmed ✅',
                'confirmation_email_content': '''Hi {{client_first_name}},

Thank you for your booking!

Your appointment is confirmed for:
Date: {{date_of_appointment}}
Time: {{time_of_appointment}}
Service: {{service_name}}
Address: {{address_of_appointment}}

If you have any questions feel free to reply to this email

Looking forward to seeing you soon
— The {{business_name}} Team

If you have allowed appointment modifications or cancellations your clients will be able to access their customer portal directly through this email''',
                'modification_email_subject': 'Your appointment has been updated ✅',
                'modification_email_content': '''Hi {{client_first_name}},

Your appointment has been successfully updated

Previous date and time: {{previous_date_of_appointment}} at {{previous_time_of_appointment}}
New date and time: {{date_of_appointment}} at {{time_of_appointment}}
Service: {{service_name}}
Address: {{address_of_appointment}}

If you have any questions or need to make further changes feel free to reply to this email

We look forward to seeing you soon
— The {{business_name}} Team''',
                'cancellation_email_subject': 'Your appointment has been canceled ❌',
                'cancellation_email_content': '''Hi {{client_first_name}},

Your appointment scheduled for
Date: {{date_of_appointment}}
Time: {{time_of_appointment}}
Service: {{service_name}}
Address: {{address_of_appointment}}
has been successfully canceled

If this was a mistake or you'd like to rebook you can use your customer portal or contact us

Take care
— The {{business_name}} Team''',
                'reminder_email_subject': 'Reminder - Your appointment is coming up 📅',
                'reminder_email_content': '''Hi {{client_first_name}},

This is a quick reminder that you have an upcoming appointment scheduled for:
Date: {{date_of_appointment}}
Time: {{time_of_appointment}}
Service: {{service_name}}
Address: {{address_of_appointment}}

If you need to reschedule or cancel feel free to use your customer portal or reply to this email

We look forward to seeing you soon
— The {{business_name}} Team'''
            }
            return Response({'data': default_template}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching communication templates: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_templates(self, request):
        try:
            organization_id = request.data.get('organization_id')

            # Extract all template fields individually to ensure each is saved
            booking_sms_content = request.data.get('booking_sms_content', '')
            confirmation_email_subject = request.data.get('confirmation_email_subject', '')
            confirmation_email_content = request.data.get('confirmation_email_content', '')
            modification_email_subject = request.data.get('modification_email_subject', '')
            modification_email_content = request.data.get('modification_email_content', '')
            cancellation_email_subject = request.data.get('cancellation_email_subject', '')
            cancellation_email_content = request.data.get('cancellation_email_content', '')
            reminder_email_subject = request.data.get('reminder_email_subject', '')
            reminder_email_content = request.data.get('reminder_email_content', '')

            with transaction.atomic():
                # Get or create the template
                template, created = CommunicationTemplate.objects.get_or_create(
                    organization_id=organization_id
                )

                # Save each template field separately to ensure all are persisted
                template.booking_sms_content = booking_sms_content
                template.confirmation_email_subject = confirmation_email_subject
                template.confirmation_email_content = confirmation_email_content
                template.modification_email_subject = modification_email_subject
                template.modification_email_content = modification_email_content
                template.cancellation_email_subject = cancellation_email_subject
                template.cancellation_email_content = cancellation_email_content
                template.reminder_email_subject = reminder_email_subject
                template.reminder_email_content = reminder_email_content
                template.save()

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 10)
                organization.save()

                serializer = self.get_serializer(template)
                return Response({
                    'message': 'Communication templates saved',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving communication templates: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = OrganizationFAQ.objects.all()
    serializer_class = OrganizationFAQSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            faqs = OrganizationFAQ.objects.filter(organization_id=organization_id).order_by('id')
            serializer = self.get_serializer(faqs, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching FAQs: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def bulk_save(self, request):
        try:
            organization_id = request.data.get('organization_id')
            faqs_data = request.data.get('faqs', [])

            if not organization_id:
                return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Get existing FAQ IDs from request
                request_faq_ids = [faq.get('id') for faq in faqs_data if faq.get('id')]

                # Delete FAQs that are not in the request (user deleted them)
                OrganizationFAQ.objects.filter(
                    organization_id=organization_id
                ).exclude(id__in=request_faq_ids).delete()

                # Create or update FAQs
                for faq_data in faqs_data:
                    faq_id = faq_data.get('id')
                    if faq_id:
                        # Update existing FAQ
                        try:
                            faq = OrganizationFAQ.objects.get(id=faq_id, organization_id=organization_id)
                            faq.question = faq_data.get('question', faq.question)
                            faq.answer = faq_data.get('answer', faq.answer)
                            faq.save()
                        except OrganizationFAQ.DoesNotExist:
                            # Create if not found
                            OrganizationFAQ.objects.create(
                                organization_id=organization_id,
                                question=faq_data.get('question'),
                                answer=faq_data.get('answer')
                            )
                    else:
                        # Create new FAQ
                        OrganizationFAQ.objects.create(
                            organization_id=organization_id,
                            question=faq_data.get('question'),
                            answer=faq_data.get('answer')
                        )

                # Update organization step
                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 11)
                organization.save()

                # Return updated FAQs
                faqs = OrganizationFAQ.objects.filter(organization_id=organization_id).order_by('id')
                serializer = self.get_serializer(faqs, many=True)

                return Response({
                    'message': 'FAQs saved successfully',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving FAQs: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssistantViewSet(viewsets.ModelViewSet):
    queryset = Assistant.objects.all()
    serializer_class = AssistantSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assistant = Assistant.objects.filter(organization_id=organization_id).first()
            if assistant:
                serializer = self.get_serializer(assistant)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'data': None}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching assistant: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_assistant(self, request):
        try:
            organization_id = request.data.get('organization_id')
            assistant_data = {
                'name': request.data.get('name', ''),
                'voice_type': request.data.get('voice_type', ''),
                'greeting_message': request.data.get('greeting_message', ''),
            }

            with transaction.atomic():
                assistant, created = Assistant.objects.update_or_create(
                    organization_id=organization_id,
                    defaults=assistant_data
                )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 12)
                organization.save()

                serializer = self.get_serializer(assistant)
                return Response({
                    'message': 'Assistant settings saved',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving assistant: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FallbackNumberViewSet(viewsets.ModelViewSet):
    queryset = FallbackNumber.objects.all()
    serializer_class = FallbackNumberSerializer

    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fallback_numbers = FallbackNumber.objects.filter(organization_id=organization_id)
            serializer = self.get_serializer(fallback_numbers, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching fallback numbers: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def save_fallback(self, request):
        try:
            organization_id = request.data.get('organization_id')
            phone_number = request.data.get('phone_number', '')
            reasons = request.data.get('reasons', [])

            with transaction.atomic():
                # Delete existing fallback numbers
                FallbackNumber.objects.filter(organization_id=organization_id).delete()

                # Create new fallback numbers for each reason
                for reason in reasons:
                    if reason != 'no-transfer':
                        FallbackNumber.objects.create(
                            organization_id=organization_id,
                            phone_number=phone_number,
                            reason=reason
                        )

                organization = Organization.objects.get(id=organization_id)
                organization.current_step = max(organization.current_step, 13)
                organization.save()

                # Return updated fallback numbers
                fallback_numbers = FallbackNumber.objects.filter(organization_id=organization_id)
                serializer = self.get_serializer(fallback_numbers, many=True)

                return Response({
                    'message': 'Fallback numbers saved',
                    'data': serializer.data,
                    'current_step': organization.current_step
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error saving fallback numbers: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
