from datetime import date

from .models import BookingSettings, Ticket


def get_booking_settings_for_user(user):
    try:
        return BookingSettings.objects.get(assigned_user=user)
    except BookingSettings.DoesNotExist:
        return BookingSettings(assigned_user=user)
    

def get_ticket_description_for_customer(ticket):
    assigned_user = ticket.assigned_user
    user_name = "Termin bei " + assigned_user.first_name + " " + assigned_user.last_name
    if user_name.strip() == "Termin bei":
        user_name = "Termin"
    return user_name


def delete_old_tickets():
    today = date.today()
    tickets = Ticket.objects.filter(expiry__lt=today)
    tickets_to_delete = []
    for ticket in tickets:
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