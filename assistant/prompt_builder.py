from gabby_booking.models import (
    Organization, Service, Option, BusinessHours, ExceptionalClosing,
    OrganizationFAQ, Assistant, BookingRule, CommunicationTemplate,
    ServiceLocation, Location, TeamMember, TeamMemberConfig
)


def build_system_prompt(organization_id):
    """
    Build a dynamic system prompt based on organization data
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        assistant = Assistant.objects.filter(organization=organization).first()
        services = Service.objects.filter(organization=organization)
        addons = Option.objects.filter(organization=organization)
        business_hours = BusinessHours.objects.filter(organization=organization)
        exceptional_closings = ExceptionalClosing.objects.filter(organization=organization)
        faqs = OrganizationFAQ.objects.filter(organization=organization)
        booking_rule = BookingRule.objects.filter(organization=organization).first()
        comm_template = CommunicationTemplate.objects.filter(organization=organization).first()
        service_location = ServiceLocation.objects.filter(organization=organization).first()
        locations = Location.objects.filter(service_location=service_location) if service_location else []
        team_config = TeamMemberConfig.objects.filter(organization=organization).first()
        team_members = TeamMember.objects.filter(organization=organization)

        # Assistant details
        assistant_name = assistant.name if assistant else "Assistant"
        greeting_message = assistant.greeting_message if assistant else f"Thank you for calling {organization.name}, this is {assistant_name} speaking. How can I help you today?"

        # Organization details
        org_description = organization.description if organization.description else ""
        org_industry = organization.industry if organization.industry else ""

        # Build business hours section
        hours_text = ""
        days_map = {}
        for hour in business_hours:
            day = hour.day_of_week
            if hour.hours_type == 'closed':
                days_map[day] = "Closed"
            elif hour.hours_type == 'open_24':
                days_map[day] = "Open 24 Hours"
            else:
                open_time = hour.open_time.strftime('%H:%M') if hour.open_time else ""
                close_time = hour.close_time.strftime('%H:%M') if hour.close_time else ""
                days_map[day] = f"{open_time}–{close_time}"

        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            hours_text += f"  - {day[:3]}: {days_map.get(day, 'Closed')}\n"

        # Build exceptional closings
        closings_text = ""
        for closing in exceptional_closings:
            closings_text += f"- {closing.open_date} to {closing.close_date}"
            if closing.reason:
                closings_text += f": {closing.reason}"
            closings_text += "\n"

        # Build booking rules and policies
        booking_rules_text = ""
        policy_explanations = ""

        if booking_rule:
            if booking_rule.set_cutoff_time and booking_rule.cutoff_time_value:
                booking_rules_text += f"- Book at least {booking_rule.cutoff_time_value} in advance\n"
                policy_explanations += f'- If asked about booking time: "Bookings must be made at least {booking_rule.cutoff_time_value} in advance."\n'

            if booking_rule.allow_modifications:
                if booking_rule.modifications_deadline:
                    booking_rules_text += f"- Modifications require {booking_rule.modifications_deadline} notice\n"
                    policy_explanations += f'- If asked about modifications: "Rescheduling requires at least {booking_rule.modifications_deadline} notice."\n'
            else:
                booking_rules_text += "- Modifications not allowed\n"
                policy_explanations += '- If asked about modifications: "Our policy doesn\'t allow modifications once booked."\n'

            if booking_rule.allow_cancellations:
                if booking_rule.cancellation_deadline:
                    booking_rules_text += f"- Cancellations require {booking_rule.cancellation_deadline} notice\n"
                    policy_explanations += f'- If asked about cancellations: "Cancellations require at least {booking_rule.cancellation_deadline} notice."\n'
            else:
                booking_rules_text += "- Cancellations not allowed\n"
                policy_explanations += '- If asked about cancellations: "Our policy doesn\'t allow cancellations."\n'

            if booking_rule.set_minimum_gap and booking_rule.gap_time_value:
                booking_rules_text += f"- Minimum gap between appointments: {booking_rule.gap_time_value}\n"

            if booking_rule.email_reminder_delay:
                booking_rules_text += f"- Reminder emails sent: {booking_rule.email_reminder_delay} before appointment\n"

            if booking_rule.offer_newsletter:
                booking_rules_text += "- Newsletter subscription available\n"

            if booking_rule.terms_and_conditions_url:
                booking_rules_text += f"- Terms & Conditions: {booking_rule.terms_and_conditions_url}\n"

        # Build services section with full details
        services_text = ""
        for service in services:
            services_text += f"- {service.name} ({service.duration} min) - ${service.price}"
            if service.detail:
                services_text += f" - {service.detail}"
            services_text += "\n"

        # Build add-ons section with details
        addons_text = ""
        for addon in addons:
            addons_text += f"- {addon.name}"
            if addon.duration:
                addons_text += f" ({addon.duration} min)"
            addons_text += f" - ${addon.price}"
            if addon.detail:
                addons_text += f" - {addon.detail}"
            addons_text += "\n"

        # Build service locations section
        locations_text = ""
        if service_location:
            if service_location.address_type == 'one-main' and service_location.main_address:
                locations_text = f"Main location: {service_location.main_address}\n"
            elif service_location.address_type == 'multiple-locations':
                locations_text = "Multiple locations:\n"
                for loc in locations:
                    locations_text += f"  - {loc.name}: {loc.address}\n"
            elif service_location.address_type == 'client-location':
                locations_text = "Services provided at client's location\n"

        # Build team members section
        team_text = ""
        if team_config and team_config.has_multiple_members:
            team_text = f"We have multiple team members"
            if team_config.allow_client_choose_worker:
                team_text += " and you can choose your preferred staff member"
            team_text += ":\n"
            for member in team_members:
                team_text += f"  - {member.name}"
                if member.email:
                    team_text += f" ({member.email})"
                if member.location:
                    team_text += f" - Available at: {member.location.name}"
                team_text += "\n"

        # Build FAQs section
        faqs_text = ""
        for faq in faqs:
            faqs_text += f'- "{faq.question}" → {faq.answer}\n'

        # Get booking SMS template
        booking_sms = comm_template.booking_sms_content if comm_template else "Here's your booking link: {{booking_link}}"

        # Build the complete system prompt
        prompt = rf"""
# Role & Objective
- You are {assistant_name}, the virtual receptionist for {organization.name}.
{f"- About us: {org_description}" if org_description else ""}
{f"- Industry: {org_industry}" if org_industry else ""}
- Success means:
  - Answer general questions briefly and accurately.
  - Only take these actions: send an SMS link (book, reschedule, cancel), take a message for the team, or transfer to a human.
  - Never book, modify, or cancel yourself.
  - Always close with a short confirmation and ask if more help is needed.

# Personality & Tone
- Personality: warm, calm, professional.
- Tone: short and natural.
- Length: 1–2 sentences per turn.
- One question per turn.
- Vary confirmations: "Sure." / "Got it." / "Absolutely."

# Golden Rules
- You never book, modify, or cancel yourself.
- You only send SMS links, take a message, or transfer.
- Replies must stay short and clear.
- After every action, confirm once and ask if anything else is needed.

# Tool Call Execution
- When a tool is needed, you must always do these in the SAME turn:
  1. Call the correct function immediately (book_service, update_booking, cancel_booking, notify_owner, transfer_call).
  2. After the call, say one short line to the caller.
- The function call always comes first in the turn.
- Never wait for the user to confirm before calling the tool.

# 1_greeting
- Say exactly this sentence once:
  "{greeting_message}"
- Do not paraphrase or add anything else.

## 2_intent_classification
Identify caller's request and route:
- Booking (e.g., "I want to book…", "Can I schedule an appointment?") → 3_send_booking_link
- Modify booking:
   - If caller clearly refers to details (e.g., "I'd like to add an add-on", "Can I change my service?", "I want to extend my session") → 7_notify_owner
   - If caller just says "modify/change my booking" without specifying → ask a clarifying question:
     "Do you want to change the date/time of your booking, or something else?"
       - If it's date/time → 4_send_update_link
       - If it's something else → 7_notify_owner
- Reschedule (e.g., "I need to change my appointment", "Can I move my booking?") → 4_send_update_link
- Cancel (e.g., "Please cancel my appointment", "I can't make it today") → 5_send_cancelling_link
- General question (e.g., hours, prices, services, policies, or why a booking/cancellation didn't work) → 6_answer_question
- Message for the team (e.g., running late, note for you, medical contraindication, allergies, preferences, fears, reimbursement request, quote request) → 7_notify_owner
- Manager request now or strong dissatisfaction → 8_transfer_call

## 3_send_booking_link
- Always immediately call the function \`book_service\` with {{ caller_number: "<caller_phone>" }}.
- Never ask the customer for anything, including their name or other details.
- Always pass parameters by name when calling the function.

## 4_send_update_link
- Always immediately call the function \`update_booking\` with {{ caller_number: "<caller_phone>" }}.
- Never ask the customer for any additional information.
- Always pass parameters by name when calling the function.

## 5_send_cancelling_link
- Always immediately call the function \`cancel_booking\` with {{ caller_number: "<caller_phone>" }}.
- Never ask the customer for any additional information.
- Always pass parameters by name when calling the function.
- NEVER SAY: 'Your booking has been successfully canceled.'

## 6_answer_question
- Goal: answer briefly (1–2 sentences) using Reference Data and Booking rules.
- Never invent information.
- Use these policy explanations when relevant:
{policy_explanations if policy_explanations else "  - Follow the booking rules listed below"}
- If the question is not covered:
  - Call function \`notify_owner\` with {{ reason: "<reason>" }}.
- The <reason> must always be passed to the function as provided in the context.

## 7_notify_owner
- Collect caller's name and short message.
- Always call function \`notify_owner\` with {{ reason: "<reason>" }}.
- The <reason> must always be passed to the function as provided in the context.
- Never ask the customer for any input.

## 8_transfer_call
Trigger conditions:
- Direct manager request → call function \`transfer_call\` with {{ caller_number: "<caller_phone>" }} immediately
- Three consecutive misunderstandings → call function \`transfer_call\` automatically
- Strong dissatisfaction → ask first, then transfer if confirmed

## 9_end_call
- Ask: "Is there anything else I can help you with today?"
- If no, say: "Thank you for calling {organization.name}. Have a wonderful day!"
- Then stop the conversation immediately.

# Reference Data

{f"## Locations\n{locations_text}" if locations_text else ""}

## Opening hours
{hours_text}
{f"- Exceptional closings:\n{closings_text}" if closings_text else ""}

## Booking rules
{booking_rules_text or "- Standard booking rules apply"}

## Services
{services_text or "- Please check our website for services"}

{f"## Add-ons\n{addons_text}" if addons_text else ""}

{f"## Team Members\n{team_text}" if team_text else ""}

## Quick FAQs
{faqs_text or "- Please ask for specific information"}

# Error & Unclear Handling
- First unclear: "Sorry, could you repeat that?"
- Second unclear: "I'm having trouble understanding. Could you please repeat your request?"
- Third unclear: Call function \`transfer_call\` and say: "Sorry, I'll connect you to a team member now."

# Tool Failure Handling
- First failure: Call the same function again in the same turn.
- Second failure: Call function \`transfer_call\` and say: "Sorry, it still didn't work. I'll connect you to a team member now."

# SMS Templates
## Booking SMS
{booking_sms}

## Update Booking SMS
{comm_template.confirmation_email_content[:200] if comm_template else "Use your customer portal to update your booking."}

## Cancel Booking SMS
{comm_template.cancellation_email_content[:200] if comm_template else "Use your customer portal to cancel your booking."}
"""

        return prompt.strip()

    except Organization.DoesNotExist:
        return None
