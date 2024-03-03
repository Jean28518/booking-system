from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import root.templates as templates
import datetime

from .models import Calendar, Ticket
import booking.forms as forms
import booking.calendar



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
    return render(request, "booking/ticket_customer_view.html", {"ticket": ticket})


@login_required()
def tickets(request):
    tickets = Ticket.objects.filter(assigned_user=request.user)
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
    return render(request, "root/message.html", {"message": "Ticket gelöscht", "url": reverse("tickets")})


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