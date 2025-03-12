from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponse, HttpResponseRedirect
import root.templates as templates
import datetime
from booking.timezones import common_timezones_array_of_dicts, convert_time_from_local_to_utc, convert_time_from_utc_to_local


from .models import Calendar, Ticket
import booking.forms as forms
import booking.calendar
import booking.caldav
import booking.booking
from django.utils.translation import gettext as _

from django.contrib.auth.models import User


@login_required()
def index(request):
    _load_timezone_for_request(request)
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
            return templates.message(request, _("Error: Please fill out all fields"))
        recurring = request.POST.get("recurring", "") == "on"
        ticket = Ticket(name=name, first_available_date=start_date, duration=duration, expiry=expiry_date, generate_jitsi_link=generate_jitsi_link, assigned_user=request.user, guid=guid, recurring=recurring)
        ticket.save()
        share_url = settings.BASE_URL + reverse("ticket_customer_view", args=[ticket.guid])
        return render(request, "booking/ticket_created.html", {"ticket": ticket, "share_url": share_url})

    booking.booking.delete_old_tickets()
    default_name = _("Ticket from") + " " + datetime.datetime.now().strftime("%d.%m.%Y %H:%M") + " " + _("APPENDIX_AFTER_TIME")
    start_date = datetime.date.today().strftime("%Y-%m-%d")
    expiry_date = (datetime.date.today() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
    return render(request, 'booking/index.html', {"start_date": start_date, "expiry_date": expiry_date, "default_name": default_name})

@login_required()
def calendars(request):
    # Convert to list
    calendars = list(Calendar.objects.filter(assigned_user=request.user))

    overview = templates.process_overview_dict({
        "heading": _("Calendars"),
        "element_name": _("Calendar"),
        "elements": calendars,
        "element_url_key": "id",
        "t_headings": [_("Name"), _("Main Calendar")],
        "t_keys": ["name", "main_calendar"],
        "add_url_name": "create_calendar",
        "edit_url_name": "edit_calendar",
        "delete_url_name": "delete_calendar",
    })
    # If no calendar is set as main calendar, display message
    if not booking.calendar.get_main_calendar_for_user(request.user):
        print("FALSE!")
        overview["message"] = _("No main calendar has been set. This is necessary to save bookings.")

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
            return render(request, "root/message.html", {"message": _("Calendar successfully created"), "url": reverse("calendars")})
        else:
            message = _("Error creating calendar")
    return render(request, 'root/create_x.html', {"element_name": _("Calendar"), "form": form, "back": reverse("calendars"), "message": message})

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
            return render(request, "root/message.html", {"message": _("Changes saved"), "url": reverse("calendars")})
        else:
            message = _("Error editing calendar")
    return render(request, 'root/edit_x.html', {"name": calendar.name, "form": form, "back": reverse("calendars"), "message": message})


@login_required()
def delete_calendar(request, calendar_id):
    calendar = Calendar.objects.get(id=calendar_id)
    calendar.delete()
    return render(request, "root/message.html", {"message": _("Calendar deleted"), "url": reverse("calendars")})

def recurring_ticket(request, guid):
    _load_timezone_for_request(request)
    # Look if ticket exists
    try:
        ticket = Ticket.objects.get(guid=guid)
    except Ticket.DoesNotExist:
        return templates.message(request, _("The ticket has expired."), "index")
    if not ticket.recurring:
        return templates.message(request, _("This is not a recurring ticket."), "ticket_customer_view", [guid])
    
    # Get all tickets which belong to this recurring ticket
    tickets = Ticket.objects.filter(parent_ticket=ticket)
    tickets = list(tickets)
    # Sort tickets by creation. The newest ticket should be on top.
    # (The id is automatically incremented by the database, so we can use this as a timestamp for the creation date.)
    tickets.sort(key=lambda x: x.id, reverse=True)
    ticket_dicts = []
    for ticket in tickets:
        ticket_dict = {
            "name": ticket.name,
            "duration": ticket.duration,
            "current_date": ticket.current_date,
            "current_date_ticket_user": convert_time_from_utc_to_local(ticket.current_date, ticket.assigned_user.profile.timezone),
            "guid": ticket.guid,
        }
        ticket_dicts.append(ticket_dict)
    overview = templates.process_overview_dict({
        "heading": _("Appointments with") + " " + ticket.assigned_user.first_name + " " + ticket.assigned_user.last_name,
        "element_name": _("Ticket"),
        "elements": ticket_dicts,
        "element_url_key": "guid",
        "t_headings": [_("Name"), _("Duration"), _("Booked Date")],
        "t_keys": ["name", "duration", "current_date_ticket_user"],
        "edit_url_name": "customer_change_date", 
        "delete_url_name": "delete_ticket",
        "hint": '<a href="{}" role="button">{}</a>'.format(reverse("create_ticket_from_recurring", args=[guid]), _("Create a new appointment")),
    })
    print(overview["hint"])
    return render(request, 'root/overview_x.html', {"overview": overview, "timezones": common_timezones_array_of_dicts})
   
   
def create_ticket_from_recurring(request, guid):
    _load_timezone_for_request(request)
    # Look if ticket exists
    try:
        parent_ticket = Ticket.objects.get(guid=guid)
    except Ticket.DoesNotExist:
        return templates.message(request, _("The ticket has expired."), "index")
    if not parent_ticket.recurring:
        return templates.message(request, _("This is not a recurring ticket."), "ticket_customer_view", [guid])
    form = forms.TicketCustomerForm()
    if request.method == "POST":
        form = forms.TicketCustomerForm(request.POST)
        guid = booking.calendar.generate_guid()

        if form.is_valid():
            # Check if duration is bigger than the duration of the parent ticket
            if int(form.cleaned_data["duration"]) > parent_ticket.duration.seconds // 60:
                return templates.message(request, _("The duration is too long. Please select a shorter duration."), "recurring_ticket", [guid])
            new_ticket = Ticket(name=parent_ticket.name + ": " + form.cleaned_data["description"],
                                first_available_date=datetime.date.today(),
                                duration=datetime.timedelta(minutes=int(form.cleaned_data["duration"])),
                                expiry=(datetime.date.today() + datetime.timedelta(days=14)),
                                generate_jitsi_link=form.cleaned_data["generate_jitsi_link"] == "on",
                                assigned_user=parent_ticket.assigned_user, 
                                email_of_customer=parent_ticket.email_of_customer,
                                guid=guid,
                                parent_ticket=parent_ticket,
                                recurring=False)
            new_ticket.save()
            share_url = settings.BASE_URL + reverse("ticket_customer_view", args=[new_ticket.guid])
            return HttpResponseRedirect(share_url)
    # Remove all the durations of the form select which are higher than the duration in the parent ticket
    choices_for_customer = []
    for choice in form.fields["duration"].choices:
        print(choice)
        print(choice[0], parent_ticket.duration.seconds // 60)
        if choice[0] <= parent_ticket.duration.seconds // 60:
            choices_for_customer.append(choice)
            print("Append")
    form.fields["duration"].choices = choices_for_customer
    # Set the initial choice to the highest possible duration
    form.fields["duration"].initial = parent_ticket.duration.seconds // 60

    form.fields["description"].initial = _("Ticket from") + " " + datetime.datetime.now().strftime("%d.%m.%Y")

    return render(request, 'root/create_x.html', {"element_name": _("Appointment"), "form": form, "back": reverse("recurring_ticket", args=[guid])})


def ticket_customer_view(request, guid):
    _load_timezone_for_request(request)
    # Look if ticket exists
    try:
        ticket = Ticket.objects.get(guid=guid)
    except Ticket.DoesNotExist:
        return templates.message(request, _("The ticket has expired."), "index")
    
    # Add handling for recurring tickets
    if ticket.recurring:
        return HttpResponseRedirect(reverse("recurring_ticket", args=[guid]))

    if ticket.current_date:
        ticket_datetime = ticket.current_date
        ticket_datetime_customer = convert_time_from_utc_to_local(ticket_datetime, request.session["django_timezone"])
        date_display = ticket_datetime_customer.strftime("%d.%m.%Y")
        start_time_display = ticket_datetime_customer.strftime("%H:%M")
        duration_display = ticket.duration.seconds // 60
        jitsi_link = booking.booking.get_jitsi_link_for_ticket(ticket)
        return render(request, "booking/ticket_customer_view.html", {"ticket": ticket, "date_display": date_display, "start_time_display": start_time_display, "duration_display": duration_display, "jitsi_link": jitsi_link, "timezones": common_timezones_array_of_dicts})
    weeks = booking.calendar.get_available_slots_for_ticket(ticket, request.session["django_timezone"], request)
    slots = []
    for week in weeks:
        for day in week:
            date = day["date"]
            for slot in day.get("slots", []):
                slots.append((date.strftime("%d.%m.%Y"), slot["start"].strftime("%H:%M:%S")))
    request.session["slots"] = slots
    request.session["ticket_guid"] = guid
    request.session["now"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render(request, "booking/select_slot.html", {"weeks": weeks, "ticket": ticket, "timezones": common_timezones_array_of_dicts})


@login_required()
def tickets(request):
    _load_timezone_for_request(request)
    tickets = Ticket.objects.filter(assigned_user=request.user)
    tickets = list(tickets)
    # Sort tickets by creation. The newest ticket should be on top.
    # (The id is automatically incremented by the database, so we can use this as a timestamp for the creation date.)
    tickets.sort(key=lambda x: x.id, reverse=True)
    ticket_dicts = []
    for ticket in tickets:
        ticket_dict = {
            "name": ticket.name,
            "duration": ticket.duration,
            "current_date": ticket.current_date,
            "current_date_ticket_user": convert_time_from_utc_to_local(ticket.current_date, ticket.assigned_user.profile.timezone),
            "guid": ticket.guid,
            "recurring": ticket.recurring,
        }
        ticket_dicts.append(ticket_dict)
    overview = templates.process_overview_dict({
        "heading": _("Tickets"),
        "element_name": _("Ticket"),
        "elements": ticket_dicts,
        "element_url_key": "guid",
        "t_headings": [_("Name"), _("Duration"), _("Booked Date"), _("Recurring")],
        "t_keys": ["name", "duration", "current_date_ticket_user", "recurring"],
        "add_url_name": "index",
        "edit_url_name": "edit_ticket", 
        "delete_url_name": "delete_ticket",
        "hint": _("Tickets can also be shared via the link"),
    })
    return render(request, 'root/overview_x.html', {"overview": overview, "timezones": common_timezones_array_of_dicts})


def delete_ticket(request, guid):
    try:
        ticket = Ticket.objects.get(guid=guid)
    except Ticket.DoesNotExist:
        return templates.message(request, _("The ticket has expired."), "index")
    # If this is not made by a recurring ticket, we need to check if the user is logged in
    if not ticket.parent_ticket:
        # Check if the user is logged in
        if not request.user.is_authenticated:
            return templates.message(request, _("You need to be logged in to delete a ticket."), "index")
        # Remove the calndar event if it exists
        booking.calendar.remove_booking(guid)
        ticket.delete()
        return redirect("tickets")
    # If this is a recurring ticket, we delete the ticket but redirect to the recurring ticket view
    parent_guid = ticket.parent_ticket.guid
    booking.calendar.remove_booking(guid)
    ticket.delete()
    return redirect("recurring_ticket", guid=parent_guid)


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
            return render(request, "root/message.html", {"message": _("Changes saved"), "url": reverse("tickets")})
        else:
            message = _("Error editing ticket")
    form.fields['ticket_customer_link'].initial = settings.BASE_URL + reverse("ticket_customer_view", args=[guid])
    form.fields['first_available_date'].initial = ticket.first_available_date.strftime("%Y-%m-%d")
    form.fields['expiry'].initial = ticket.expiry.strftime("%Y-%m-%d")
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
            message = _("Changes saved.")
        else:
            message = _("Error editing settings.")

    return render(request, 'root/generic_form.html', {
        "title": _("Booking Settings"),
        "form": form,
        "back": reverse("index"),
        "message": message,
        "submit": _("Save"),
        "display_buttons_at_top": True,
        "timezones": common_timezones_array_of_dicts
    })

    
def select_slot(request, guid, date, start_time):
    _load_timezone_for_request(request)
    ticket = Ticket.objects.get(guid=guid)
    start_time = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    duration_display = ticket.duration.seconds // 60

    # Convert it to utc
    start_time_customer = start_time
    date_customer = date

    start_time = convert_time_from_local_to_utc(datetime.datetime.combine(date, start_time), request.session["django_timezone"]).time()
    date = convert_time_from_local_to_utc(datetime.datetime.combine(date, start_time), request.session["django_timezone"]).date()

    start_time_ticket_user = convert_time_from_utc_to_local(datetime.datetime.combine(date, start_time), ticket.assigned_user.profile.timezone).time()
    date_ticket_user = convert_time_from_utc_to_local(datetime.datetime.combine(date, start_time), ticket.assigned_user.profile.timezone).date()

    if request.method == "POST":
        # Check if the selected slot is still available (disabled because of some errors, we get)
        # if ticket.current_date == None and not booking.calendar.is_slot_available(guid, date, start_time):
        #     return templates.message(request, _("An error occurred. Please select another slot."), "ticket_customer_view", [guid])

        # Check if the guid in session is the same as the guid in the url
        if request.session["ticket_guid"] != guid:
            return templates.message(request, _("An error occurred. Please select another slot."), "ticket_customer_view", [guid])
        # and session[now] is younger than 5 minutes
        session_now = datetime.datetime.strptime(request.session["now"], "%Y-%m-%d %H:%M:%S")
        if (datetime.datetime.now() - session_now).seconds > 300:
            return templates.message(request, _("Your session has expired. Please select a slot again."), "ticket_customer_view", [guid])
        # Also check if the date and start_time_customer can be found in the presented slots
        slot_found = False
        for slot in request.session.get("slots", []):
            if slot[0] == date_customer.strftime("%d.%m.%Y") and slot[1] == start_time_customer.strftime("%H:%M:%S"):
                slot_found = True
                break
        if not slot_found:
            return templates.message(request, _("An error occurred. Please select another slot!"), "ticket_customer_view", [guid])
        
        ticket.current_date = datetime.datetime.combine(date, start_time)
        ticket.email_of_customer = request.POST.get("email", "")
        ticket.save()
        if ticket.email_of_customer and ticket.parent_ticket:
            ticket.parent_ticket.email_of_customer = ticket.email_of_customer
        booking.calendar.book_ticket(guid)
        assigned_user = ticket.assigned_user
        current_datetime = ticket.current_date
        current_datetime_ticket_user = datetime.datetime.combine(date_ticket_user, start_time_ticket_user)
        current_datetime_customer = datetime.datetime.combine(date_customer, start_time_customer)
        meeting_link_description = ""
        if ticket.generate_jitsi_link:
            meeting_link_description = f"\n" + _("Link to the meeting") + f" (Jitsi): {booking.booking.get_jitsi_link_for_ticket(ticket)}"
        send_mail(
            _("Appointment") + ' "' + ticket.name + '" ' + _("booked. Date: ") + current_datetime_ticket_user.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME"),
            _("The appointment was booked on") + " " + current_datetime_ticket_user.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + meeting_link_description,
            settings.EMAIL_HOST_USER,
            [assigned_user.email],
            fail_silently=True,
        )
        ticket_description = booking.booking.get_ticket_description_for_customer(ticket)
        # Add the description of the customer which he could set in tickets which are created from a recurring ticket to the ical event
        if ticket.parent_ticket:
            attachment_ics = booking.calendar.get_ical_string_for_ticket(ticket.guid, ": " + ticket.name)
        else:
            attachment_ics = booking.calendar.get_ical_string_for_ticket(ticket.guid) 
        if ticket.email_of_customer:
            email = EmailMessage(
                f'{ticket_description} ' + _("booked. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME"),
                f'{ticket_description} ' + _("booked. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + f' ' + _("with a duration of") + f' {duration_display} ' + _("minutes") + f'.{meeting_link_description}\n\n' + _("Hint: You can manage the appointment at any time via the following link") + f': {settings.BASE_URL + reverse("ticket_customer_view", args=[guid])}',
                settings.EMAIL_HOST_USER,
                [ticket.email_of_customer],
            )
            email.attach("event.ics", attachment_ics, "text/calendar")
            email.send()
        return redirect("ticket_customer_view", guid=guid)

    # Now we are back again in customer timezone:
    start_time_display = start_time_customer.strftime("%H:%M")
    date_display = date_customer.strftime("%d.%m.%Y")
    email_of_customer = ""
    if ticket.email_of_customer:
        email_of_customer = ticket.email_of_customer
    # Check if the parent ticket has an email address and use this as default
    if ticket.parent_ticket and ticket.parent_ticket.email_of_customer:
        email_of_customer = ticket.parent_ticket.email_of_customer
    return render(request, "booking/booking_confirmation.html", {"ticket": ticket, "date": date, "start_time": start_time, "start_time_display": start_time_display, "date_display": date_display, "duration_display": duration_display, "email_of_customer": email_of_customer})


def customer_cancel_ticket(request, guid):
    _load_timezone_for_request(request)
    ticket = Ticket.objects.get(guid=guid)
    current_datetime = ticket.current_date
    current_datetime_ticket_user = convert_time_from_utc_to_local(current_datetime, ticket.assigned_user.profile.timezone)
    current_datetime_customer = convert_time_from_utc_to_local(current_datetime, request.session["django_timezone"])
    booking.calendar.remove_booking(guid)
    assigned_user = ticket.assigned_user
    send_mail(
        _("Appointment") + ' "' + ticket.name + '" ' + _("canceled."),
        _("The appointment on") + " " + current_datetime_ticket_user.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + ' ' + _("was canceled."),
        settings.EMAIL_HOST_USER,
        [assigned_user.email],
        fail_silently=True,
    )
    ticket_description = booking.booking.get_ticket_description_for_customer(ticket)
    if ticket.email_of_customer:
        send_mail(
            f'{ticket_description} ' + _("canceled. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME"),
            f'{ticket_description} ' + _("canceled. Date: ") + current_datetime_customer.strftime("%d.%m.%Y %H:%M") + ' ' + _("APPENDIX_AFTER_TIME") + f'.\n\n' + _("Hint: You can manage the appointment at any time via the following link") + f': {settings.BASE_URL + reverse("ticket_customer_view", args=[guid])}',
            settings.EMAIL_HOST_USER,
            [ticket.email_of_customer],
            fail_silently=True,
        )
    return templates.message(request, _("Appointment canceled. If you want to book the appointment again, you will be redirected to the booking page."), "ticket_customer_view", [guid])

def set_timezone(request):
    if request.method == "POST":
        request.session["django_timezone"] = request.POST["timezone"]

        if request.user.is_authenticated:
            user = User.objects.get(id=request.user.id)
            user.profile.timezone = request.POST["timezone"]
            user.profile.save()
        print("Settimezone", request.POST["timezone"])
        # Save also the timezone in a cookie
        response = HttpResponse("Ok")
        response.set_cookie("timezone", request.POST["timezone"], max_age=10*365*24*60*60)
        return response
    else:
        return templates.message(request, _("Error: Please select a timezone."))
    
def _load_timezone_for_request(request):
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        request.session["django_timezone"] = user.profile.timezone
    else:
        # Load timezone from cookie if available
        request.session["django_timezone"] = request.COOKIES.get("timezone", "Europe/Berlin")