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
