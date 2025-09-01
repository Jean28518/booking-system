from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from booking.timezones import  convert_time_from_utc_to_local


import booking.booking
from django.utils.translation import gettext as _

from django.contrib.auth.models import User



def send_cancel_emails(ticket, customer_timezone="Europe/Berlin", send_hint=True):
    assigned_user = ticket.assigned_user
    guid = ticket.guid
    current_datetime = ticket.current_date
    current_datetime_ticket_user = convert_time_from_utc_to_local(current_datetime, ticket.assigned_user.profile.timezone)
    current_datetime_customer = convert_time_from_utc_to_local(current_datetime, customer_timezone)
    ticket_description = booking.booking.get_ticket_description_for_customer(ticket)
    private_ticket_name = ticket.name
    if ticket.parent_ticket:
        private_ticket_name = ticket.parent_ticket.name + ": " + private_ticket_name
    send_mail(
        _("Appointment") + ' "' + private_ticket_name + '" ' + _("canceled."),
        _("The appointment on") + " " + current_datetime_ticket_user.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + ' ' + _("was canceled."),
        settings.EMAIL_HOST_USER,
        [assigned_user.email],
        fail_silently=True,
    )
    ticket_description = booking.booking.get_ticket_description_for_customer(ticket)

    hint = ""
    if send_hint:
        hint = _("Hint: You can manage the appointment at any time via the following link") + f': {settings.BASE_URL + reverse("ticket_customer_view", args=[guid])}'
    
    if ticket.email_of_customer:
        send_mail(
            f'{ticket_description} ' + _("canceled. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME"),
            f'{ticket_description} ' + _("canceled. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + f'.\n\n' + hint,
            settings.EMAIL_HOST_USER,
            [ticket.email_of_customer],
            fail_silently=True,
        )