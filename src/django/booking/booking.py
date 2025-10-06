from datetime import date, timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


from .models import BookingSettings, Ticket
from django.utils.translation import gettext as _


def get_booking_settings_for_user(user):
    try:
        return BookingSettings.objects.get(assigned_user=user)
    except BookingSettings.DoesNotExist:
        return BookingSettings(assigned_user=user)
    

def get_ticket_description_for_customer(ticket):
    assigned_user = ticket.assigned_user
    user_name = _("Appointment with") + " " + assigned_user.first_name + " " + assigned_user.last_name
    if user_name.strip() == _("Appointment with") + " ":
        user_name =  _("Appointment")
    return user_name


def delete_old_tickets():
    today = date.today()
    tickets = Ticket.objects.filter(expiry__lt=today)
    tickets_to_delete = []
    for ticket in tickets:
        # Check if the booked time has also already passed
        if ticket.current_date:
            if ticket.current_date.date() < today:
                tickets_to_delete.append(ticket)
        else:
            tickets_to_delete.append(ticket)
    Ticket.objects.filter(id__in=[ticket.id for ticket in tickets_to_delete]).delete()


def get_jitsi_link_for_ticket(ticket: Ticket):
    if not ticket.generate_jitsi_link:
        return ""
    
    assigned_user = ticket.assigned_user
    booking_settings = get_booking_settings_for_user(assigned_user)
    jitsi_server = booking_settings.jitsi_server

    if jitsi_server and ticket.generate_jitsi_link:
        if jitsi_server[-1] == "/":
            jitsi_server = jitsi_server[:-1]
        return jitsi_server + "/" + ticket.guid
    elif ticket.generate_jitsi_link:
        return "https://meet.jit.si/" + ticket.guid
    else:
        return ""
    

# This function has to be called by a cronjob every 5 minutes
def send_reminder_mails():
    """Sends reminder mails to customer with tickets which appointment is tomorrow at the same time."""
    tomorrow = date.today() + timedelta(days=1)
    # Get all the tickets which are booked for tomorrow (current_date.date() == tomorrow)
    tickets = Ticket.objects.filter(current_date__date=tomorrow)
    for ticket in tickets:
        ticket_time = ticket.current_date.time()
        current_time = datetime.now().time()
        # If the current time is near to 3 minutes before the ticket time, send the mail
        if ticket_time.hour == current_time.hour and abs(ticket_time.minute - current_time.minute) <= 2:
            # Send mail to customer
            if not ticket.email_of_customer:
                continue
            guid = ticket.guid
            print("Sending reminder mail to: " + ticket.email_of_customer)
            ticket_time = ticket.current_date.time()
            # Send mail
            send_mail(
                _("Reminder: Your appointment with") + " " + ticket.assigned_user.first_name + " " + ticket.assigned_user.last_name + " " + _("is tomorrow at") + " "  + ticket_time.strftime("%H:%M") + _("APPENDIX_AFTER_TIME") + ".",
                _("You have an appointment with") + " " + ticket.assigned_user.first_name + " " + ticket.assigned_user.last_name + " " + _("tomorrow at") + " " + ticket_time.strftime("%H:%M") + _("APPENDIX_AFTER_TIME") + "." + "\n" + _("If you want to change or cancel the appointment, please visit the following link") + ":" + " " + settings.BASE_URL + reverse("ticket_customer_view", args=[guid]), 
                settings.EMAIL_HOST_ADDRESS,
                [ticket.email_of_customer],
                fail_silently=False
            )
            
        