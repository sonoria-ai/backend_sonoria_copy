import logging
from django.http import JsonResponse
from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action
from .models import RegistrationStep,Organization, Service , Option,BusinessHours , ExceptionalClosing,ReservationType,SMSSetting,GoogleCalendarSetting,OrganizationFAQ,Assistant,FallbackNumber,OrganizationPrompt
from .serializers import RegistrationStepSerializer,OrganizationSerializer, ServiceSerializer, OptionSerializer,BusinessHoursSerializer,ExceptionalClosingSerializer,ReservationTypeSerializer,SMSSettingSerializer, GoogleCalendarSettingSerializer,OrganizationFAQSerializer,AssistantSerializer,FallbackNumberSerializer
from rest_framework.response import Response
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
from django.conf import settings 
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .utils import generate_prompt

logger = logging.getLogger(__name__)


def generated_prompt(data):
    """Use OpenAI to generate a real-time prompt for appointment booking."""
    openai_api_key = settings.OPENAI_API_KEY  # Fetch API key from Django settings
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, openai_api_key=openai_api_key)

    business_name = data.get("name", "the business")
    business_description = data.get("description", "a professional service provider")

    meta_prompt = (
        f"You are an AI prompt generator. Your task is to create a well-structured and effective prompt for OpenAI’s assistant, "
        f"which will act as a business-specific AI agent. \n\n"
        f"The AI assistant will handle appointment bookings for a business named '{business_name}', which provides '{business_description}'. \n\n"
        f"Your response should be a fully formatted prompt that can be used directly in OpenAI for real-time interactions."
    )

    message = HumanMessage(content=meta_prompt)
    response = llm.invoke([message])

    return response.content
class RegistrationStepAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request):
        try:
            steps = RegistrationStep.objects.all()
            serializer = RegistrationStepSerializer(steps, many=True)
            return JsonResponse({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching registration steps: {str(e)}", exc_info=True)
            return JsonResponse({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # http://127.0.0.1:8000/api/registration-steps/
    # {
    # "organization": 1,
    # "step_number": 0,
    # "is_completed": false
    # }
    def post(self, request):
        try:
            serializer = RegistrationStepSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"New registration step created: {serializer.data}")
                return JsonResponse({"message": "Step created", "data": serializer.data}, status=status.HTTP_201_CREATED)
            logger.warning(f"Validation failed: {serializer.errors}")
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating registration step: {str(e)}", exc_info=True)
            return JsonResponse({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    # permission_classes = [IsAuthenticated]  # Require authentication

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """Get current user's organization with assistant_created status."""
        try:
            # Get first organization for the logged-in user
            # In production, you'd filter by request.user
            organization = Organization.objects.first()
            if not organization:
                return Response({"error": "No organization found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(organization)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching current organization: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        """Retrieve all organizations."""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            logger.info("Fetched all organizations successfully.")
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching organizations: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # http://127.0.0.1:8000/api/organizations/
    # {
    # "name": "Tech Solutions",
    # "business_line": "Software Development",
    # "industry": "Technology",
    # "description": "We build scalable software solutions.",
    # "registration_step": 1 
    # }

    def create(self, request, *args, **kwargs):
        """Create a new organization."""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                organization = serializer.save()
                prompt_text = generated_prompt(request.data)
                print(prompt_text)
                OrganizationPrompt.objects.create(organization=organization, generated_prompt=prompt_text)
                logger.info(f"New organization created: {serializer.data}")
                return Response({"message": "Organization created", "data": serializer.data}, status=status.HTTP_201_CREATED)
            logger.warning(f"Validation failed: {serializer.errors}")
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific organization by ID."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            logger.info(f"Fetched organization: {serializer.data}")
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving organization: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """Update an organization."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Updated organization: {serializer.data}")
                return Response({"message": "Organization updated", "data": serializer.data}, status=status.HTTP_200_OK)
            logger.warning(f"Validation failed: {serializer.errors}")
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating organization: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Delete an organization."""
        try:
            instance = self.get_object()
            instance.delete()
            logger.info(f"Deleted organization: {instance.name}")
            return Response({"message": "Organization deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting organization: {str(e)}", exc_info=True)
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['GET'])
def generate_prompt_view(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    assistant = organization.assistants.first()
    reservation_type = organization.reservation_types.first()

    data = {
        "assistant_name": assistant.name if assistant else "N/A",
        "company_name": organization.name,
        "company_industry": organization.industry,
        "company_description": organization.description,
        "type_of_reservation": reservation_type.type_choice if reservation_type else "N/A",
        "allow_modification": "Yes" if reservation_type.allow_modifications else "No",
        "modification_deadline": reservation_type.modification_deadline.strftime("%H:%M") if reservation_type.modification_deadline else "N/A",
        "allow_annulation": "Yes" if reservation_type.allow_cancellations else "No",
        "annulation_deadline": reservation_type.cancellation_deadline.strftime("%H:%M") if reservation_type.cancellation_deadline else "N/A",
        "cutoff": "Yes" if reservation_type.cutoff_time else "No",
        "call_transfer": "No transfer",
        "cutoff_deadline": reservation_type.cutoff_time.strftime("%H:%M") if reservation_type.cutoff_time else "N/A",
    }

    first_message = "Hello! How can I assist you today?"
    prompt = generate_prompt(data, first_message)

    return Response({"prompt": prompt})

        
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        logger.info("Fetching all services.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            service = self.get_object()
            logger.info(f"Fetching service with ID {pk}")
            serializer = self.get_serializer(service)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching service {pk}: {str(e)}")
            return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # http://127.0.0.1:8000/api/services/
    # {
    # "organization": 1,
    # "name": "Web Development",
    # "price": 500.00,
    # "duration": 60,
    # "details": "Full-stack web development service"
    # }

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            logger.info(f"Service created: {service.name}")
            return Response({"message": "Service created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        logger.warning(f"Service creation failed: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            service = self.get_object()
            logger.info(f"Deleting service with ID {pk}")
            service.delete()
            return Response({"message": "Service deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting service {pk}: {str(e)}")
            return Response({"error": "Failed to delete service"}, status=status.HTTP_400_BAD_REQUEST)

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        logger.info("Fetching all options.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            option = self.get_object()
            logger.info(f"Fetching option with ID {pk}")
            serializer = self.get_serializer(option)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching option {pk}: {str(e)}")
            return Response({"error": "Option not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # http://127.0.0.1:8000/api/options/
    # {
    # "organization": 1,
    # "service": 1,
    # "name": "Premium Support",
    # "price": 50.00,
    # "duration": 30,
    # "details": "24/7 support for web development"
    # }

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            option = serializer.save()
            logger.info(f"Option created: {option.name}")
            return Response({"message": "Option created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        logger.warning(f"Option creation failed: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            option = self.get_object()
            logger.info(f"Deleting option with ID {pk}")
            option.delete()
            return Response({"message": "Option deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting option {pk}: {str(e)}")
            return Response({"error": "Failed to delete option"}, status=status.HTTP_400_BAD_REQUEST)

class BusinessHoursViewSet(viewsets.ModelViewSet):
    queryset = BusinessHours.objects.all()
    serializer_class = BusinessHoursSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        logger.info("Fetching all business hours.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            business_hours = self.get_object()
            logger.info(f"Fetching business hours with ID {pk}")
            serializer = self.get_serializer(business_hours)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching business hours {pk}: {str(e)}")
            return Response({"error": "Business hours not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # http://127.0.0.1:8000/api/business-hours/
    # {
    # "organization": 1,
    # "day_of_week": "Monday",
    # "hours_type": "custom",
    # "open_time": "09:00:00",
    # "close_time": "18:00:00"
    # }


    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            business_hours = serializer.save()
            logger.info(f"Business hours created: {business_hours.organization.name} - {business_hours.day_of_week}")
            return Response({"message": "Business hours created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        logger.warning(f"Business hours creation failed: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            business_hours = self.get_object()
            logger.info(f"Deleting business hours with ID {pk}")
            business_hours.delete()
            return Response({"message": "Business hours deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting business hours {pk}: {str(e)}")
            return Response({"error": "Failed to delete business hours"}, status=status.HTTP_400_BAD_REQUEST)

class ExceptionalClosingViewSet(viewsets.ModelViewSet):
    queryset = ExceptionalClosing.objects.all()
    serializer_class = ExceptionalClosingSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        logger.info("Fetching all exceptional closings.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            exceptional_closing = self.get_object()
            logger.info(f"Fetching exceptional closing with ID {pk}")
            serializer = self.get_serializer(exceptional_closing)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching exceptional closing {pk}: {str(e)}")
            return Response({"error": "Exceptional closing not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # http://127.0.0.1:8000/api/exceptional-closings/
    # {
    # "organization": 1,
    # "open_date": "2024-12-24",
    # "close_date": "2024-12-25",
    # "reason": "Christmas Holidays"
    # }

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            exceptional_closing = serializer.save()
            logger.info(f"Exceptional closing created for {exceptional_closing.organization.name}")
            return Response({"message": "Exceptional closing created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        logger.warning(f"Exceptional closing creation failed: {serializer.errors}")
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            exceptional_closing = self.get_object()
            logger.info(f"Deleting exceptional closing with ID {pk}")
            exceptional_closing.delete()
            return Response({"message": "Exceptional closing deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting exceptional closing {pk}: {str(e)}")
            return Response({"error": "Failed to delete exceptional closing"}, status=status.HTTP_400_BAD_REQUEST)
        
class ReservationTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Reservation Types.
    """
    queryset = ReservationType.objects.all()
    serializer_class = ReservationTypeSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Fetching all reservation types")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching reservation type with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)

    # http://127.0.0.1:8000/api/reservation-types/
    # {
    #     "organization": 1,
    #     "type_choice": "sms",
    #     "cutoff_time": "18:00:00",
    #     "allow_modifications": true,
    #     "modification_deadline": "12:00:00",
    #     "allow_cancellations": true,
    #     "cancellation_deadline": "14:00:00"
    # }

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new reservation type")
        return super().create(request, *args, **kwargs)

    def update(self, request, pk=None, *args, **kwargs):
        logger.info(f"Updating reservation type with ID: {pk}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting reservation type with ID: {pk}")
        return super().destroy(request, *args, **kwargs)


class SMSSettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SMS Settings.
    """
    queryset = SMSSetting.objects.all()
    serializer_class = SMSSettingSerializer
    # permission_classes = [IsAuthenticated]

    # http://127.0.0.1:8000/api/sms-settings/
    # {
    # "reservation_type": 1,
    # "message_template": "Your booking is confirmed! Visit this link: example.com/booking"
    # }

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new SMS setting")
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching SMS setting with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting SMS setting with ID: {pk}")
        return super().destroy(request, *args, **kwargs)


class GoogleCalendarSettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Google Calendar Settings.
    """
    queryset = GoogleCalendarSetting.objects.all()
    serializer_class = GoogleCalendarSettingSerializer
    # permission_classes = [IsAuthenticated]

    # http://127.0.0.1:8000/api/google-calendar-settings/
    # {
    #     "reservation_type": 1,
    #     "google_calendar_id": "calendar123",
    #     "message_template": "Your event has been added to Google Calendar. Booking link: example.com/booking"
    # }

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new Google Calendar setting")
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching Google Calendar setting with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting Google Calendar setting with ID: {pk}")
        return super().destroy(request, *args, **kwargs)
    


class OrganizationFAQViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Organization FAQs.
    """
    queryset = OrganizationFAQ.objects.all()
    serializer_class = OrganizationFAQSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Fetching all FAQs")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching FAQ with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)
    
    # http://127.0.0.1:8000/api/organization-faqs/
    # {
    #     "organization": 1,
    #     "question": "What are the working hours?",
    #     "answer": "Our working hours are from 9 AM to 5 PM."
    # }

    def create(self, request, *args, **kwargs):
        logger.info("Creating a new FAQ")
        return super().create(request, *args, **kwargs)

    def update(self, request, pk=None, *args, **kwargs):
        logger.info(f"Updating FAQ with ID: {pk}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting FAQ with ID: {pk}")
        return super().destroy(request, *args, **kwargs)
    

class AssistantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Virtual Assistants.
    """
    queryset = Assistant.objects.all()
    serializer_class = AssistantSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Fetching all Assistants")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching Assistant with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)
    
    # http://127.0.0.1:8000/api/assist-add/
    # {
    # "organization": 1,
    # "name": "Gabby AI",
    # "voice_type": "Female - Soft"
    # }


    def create(self, request, *args, **kwargs):
        logger.info("Creating a new Assistant")
        return super().create(request, *args, **kwargs)

    def update(self, request, pk=None, *args, **kwargs):
        logger.info(f"Updating Assistant with ID: {pk}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting Assistant with ID: {pk}")
        return super().destroy(request, *args, **kwargs)


class FallbackNumberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Fallback Numbers.
    """
    queryset = FallbackNumber.objects.all()
    serializer_class = FallbackNumberSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Fetching all Fallback Numbers")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        logger.info(f"Fetching Fallback Number with ID: {pk}")
        return super().retrieve(request, *args, **kwargs)
    
    # http://127.0.0.1:8000/api/fallback-numbers/
    # {
    # "organization": 1,
    # "phone_number": "1234567890",
    # "reason": "For emergency calls"
    # }


    def create(self, request, *args, **kwargs):
        logger.info("Creating a new Fallback Number")
        return super().create(request, *args, **kwargs)

    def update(self, request, pk=None, *args, **kwargs):
        logger.info(f"Updating Fallback Number with ID: {pk}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        logger.warning(f"Deleting Fallback Number with ID: {pk}")
        return super().destroy(request, *args, **kwargs)