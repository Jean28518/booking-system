from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import root.templates as templates
import datetime
import pytz

from .models import Calendar, Ticket
import booking.forms as forms
import booking.calendar
import booking.caldav
import booking.booking

from django.contrib.auth.models import User


@login_required()
def index(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        # Parse date
        start_date = datetime.datetime.strptime(request.POST.get("start_date", ""), "%Y-%m-%d").date()
        expiry_date = datetime.datetime.strptime(request.POST.get("expiry_date", ""), "%Y-%m-%d").date()
        generate_jitsi_link = request.POST.get("generate_jitsi_link", False)
        if generate_jitsi_link == "on":
            generate_jitsi_link = True
        duration = datetime.timedelta(minutes=int(request.POST["duration"]))
        # Generate guid
        guid = booking.calendar.generate_guid()
        if start_date == "" or expiry_date == "" or duration == "" or name == "":
            return templates.message(request, "Fehler: Bitte alle Felder ausfüllen")

        ticket = Ticket(name=name, first_available_date=start_date, duration=duration, expiry=expiry_date, generate_jitsi_link=generate_jitsi_link, assigned_user=request.user, guid=guid)
        ticket.save()
        share_url = settings.BASE_URL + reverse("ticket_customer_view", args=[ticket.guid])
        return render(request, "booking/ticket_created.html", {"ticket": ticket, "share_url": share_url})

    default_name = "Ticket von " + datetime.datetime.now().strftime("%d.%m.%Y %H:%M Uhr")
    start_date = datetime.date.today().strftime("%Y-%m-%d")
    expiry_date = (datetime.date.today() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
    return render(request, 'booking/index.html', {"start_date": start_date, "expiry_date": expiry_date, "default_name": default_name})

@login_required()
def calendars(request):
    # Convert to list
    calendars = list(Calendar.objects.filter(assigned_user=request.user))

    overview = templates.process_overview_dict({
        "heading": "Kalender",
        "element_name": "Kalender",
        "elements": calendars,
        "element_url_key": "id",
        "t_headings": ["Name", "Hauptkalender"],
        "t_keys": ["name", "main_calendar"],
        "add_url_name": "create_calendar",
        "edit_url_name": "edit_calendar",
        "delete_url_name": "delete_calendar",
    })
    # If no calendar is set as main calendar, display message
    if not booking.calendar.get_main_calendar_for_user(request.user):
        print("FALSE!")
        overview["message"] = "Es wurde noch kein Hauptkalender festgelegt. Dieser ist notwendig, um Buchungen abzuspeichern."


    return render(request, 'root/overview_x.html', {"overview": overview})

@login_required()
def create_calendar(request):
    message = ""
    form = forms.CalendarForm()
    if request.method == "POST":
        form = forms.CalendarForm(request.POST)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.assigned_user = request.user
            calendar.save()
            if calendar.main_calendar:
                booking.calendar.set_main_calendar_for_user(request.user, calendar)
            return render(request, "root/message.html", {"message": "Kalender erfolgreich erstellt", "url": reverse("calendars")})
        else:
            message = "Fehler beim Erstellen des Kalenders"
    return render(request, 'root/create_x.html', {"element_name": "Kalender", "form": form, "back": reverse("calendars"), "message": message})

@login_required()
def edit_calendar(request, calendar_id):
    calendar = Calendar.objects.get(id=calendar_id)
    message = ""
    form = forms.CalendarForm(instance=calendar)
    if request.method == "POST":
        form = forms.CalendarForm(request.POST, instance=calendar)
        if form.is_valid():
            calendar = form.save(commit=False)
            calendar.assigned_user = request.user
            calendar.save()
            print(calendar.main_calendar)
            if calendar.main_calendar:
                booking.calendar.set_main_calendar_for_user(request.user, calendar)
            return render(request, "root/message.html", {"message": "Änderungen abgespeichert", "url": reverse("calendars")})
        else:
            message = "Fehler beim Bearbeiten des Kalenders"
    return render(request, 'root/edit_x.html', {"name": calendar.name, "form": form, "back": reverse("calendars"), "message": message})


@login_required()
def delete_calendar(request, calendar_id):
    calendar = Calendar.objects.get(id=calendar_id)
    calendar.delete()
    return render(request, "root/message.html", {"message": "Kalender gelöscht", "url": reverse("calendars")})


def ticket_customer_view(request, guid):
    ticket = Ticket.objects.get(guid=guid)
    if ticket.current_date:
        date_display = ticket.current_date.strftime("%d.%m.%Y")
        start_time_display = ticket.current_date.strftime("%H:%M")
        duration_display = ticket.duration.seconds // 60
        return render(request, "booking/ticket_customer_view.html", {"ticket": ticket, "date_display": date_display, "start_time_display": start_time_display, "duration_display": duration_display})
    weeks = booking.calendar.get_available_slots_for_ticket(ticket)
    return render(request, "booking/select_slot.html", {"weeks": weeks, "ticket": ticket})


@login_required()
def tickets(request):
    tickets = Ticket.objects.filter(assigned_user=request.user)
    tickets = list(tickets)
    # Sort tickets by creation. The newest ticket should be on top.
    # (The id is automatically incremented by the database, so we can use this as a timestamp for the creation date.)
    tickets.sort(key=lambda x: x.id, reverse=True)
    print(tickets)
    overview = templates.process_overview_dict({
        "heading": "Tickets",
        "element_name": "Ticket",
        "elements": tickets,
        "element_url_key": "guid",
        "t_headings": ["Name", "Dauer", "Gebuchtes Datum"],
        "t_keys": ["name", "duration", "current_date"],
        "add_url_name": "index",
        "edit_url_name": "edit_ticket", 
        "delete_url_name": "delete_ticket",
        "hint": "Tickets können auch über den Link geteilt werden",
    })
    return render(request, 'root/overview_x.html', {"overview": overview})


@login_required()
def delete_ticket(request, guid):
    ticket = Ticket.objects.get(guid=guid)
    ticket.delete()
    return redirect("tickets")


@login_required()
def edit_ticket(request, guid):
    ticket = Ticket.objects.get(guid=guid)
    message = ""
    form = forms.TicketForm(instance=ticket)
    if request.method == "POST":
        form = forms.TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.assigned_user = request.user

            # The form returns sometimes the duration in minutes and seconds, but we need this in hours and minutes
            if ticket.duration <= datetime.timedelta(minutes=10):
                minutes = ticket.duration.total_seconds() // 60
                seconds = ticket.duration.total_seconds() % 60
                print(minutes, seconds)
                ticket.duration = datetime.timedelta(hours=minutes, minutes=seconds)
                
            ticket.save()
            return render(request, "root/message.html", {"message": "Änderungen abgespeichert", "url": reverse("tickets")})
        else:
            message = "Fehler beim Bearbeiten des Tickets"
    return render(request, 'root/edit_x.html', {"name": ticket.name, "form": form, "back": reverse("tickets"), "message": message})


@login_required()
def booking_settings(request):
    settings = booking.booking.get_booking_settings_for_user(request.user)
    message = ""
    form = forms.BookingSettingsForm(instance=settings)
    if request.method == "POST":
        form = forms.BookingSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.assigned_user = request.user
            settings.save()
            message = "Änderungen abgespeichert."
        else:
            message = "Fehler beim Bearbeiten der Einstellungen."

    return render(request, 'root/generic_form.html', {"title": "Buchungseinstellungen", "form": form, "back": reverse("index"), "message": message, "submit": "Speichern", "display_buttons_at_top": True})

    
def select_slot(request, guid, date, start_time):
    ticket = Ticket.objects.get(guid=guid)
    start_time = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    if request.method == "POST":
        # Check if the selected slot is still available
        if ticket.current_date == None and not booking.calendar.is_slot_available(guid, date, start_time):
            return templates.message(request, "Ein Fehler ist aufgetreten. Bitte wählen Sie einen anderen Slot.", "ticket_customer_view", [guid])
        ticket.current_date = datetime.datetime.combine(date, start_time)
        ticket.save()
        booking.calendar.book_ticket(guid)
        return redirect("ticket_customer_view", guid=guid)

    start_time_display = start_time.strftime("%H:%M")
    date_display = date.strftime("%d.%m.%Y")
    duration_display = ticket.duration.seconds // 60
    return render(request, "booking/booking_confirmation.html", {"ticket": ticket, "date": date, "start_time": start_time, "start_time_display": start_time_display, "date_display": date_display, "duration_display": duration_display})


def customer_cancel_ticket(request, guid):
    booking.calendar.remove_booking(guid)
    return templates.message(request, "Termin erfolgreich storniert. Wenn Sie den Termin doch wahrnehmen wollen, werden Sie nun wieder zur Buchungs-Seite weitergeleitet.", "ticket_customer_view", [guid])


def customer_change_date(request, guid):
    booking.calendar.remove_booking(guid)
    return redirect("ticket_customer_view", guid=guid)
