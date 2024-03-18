import datetime
# import caldav
import booking.caldav as caldav
from booking.models import Calendar
import booking.booking
import uuid
from .models import Ticket, BookingSettings
import booking.booking as booking
import locale
import pytz

def time_to_quarter(time):
    return time.hour * 4 + time.minute // 15


def quarter_to_time(quarter):
    return datetime.time(quarter // 4, (quarter % 4) * 15)


def is_quarter_15_or_45(quarter):
    return quarter % 4 == 3 or quarter % 4 == 1


def is_quarter_30(quarter):
    return quarter % 4 == 2

def get_free_slots(events, start_time: datetime.datetime, end_time: datetime.datetime):
    """Returns a list of days, which is containing a list of free quarters for each day."""

    # Remove all events which beginnings and endings are outside the time frame and keep only these which are marked as busy
    events = [event for event in events if event["start"] < end_time and event["end"] > start_time and event["busy"]]

    # Generate a list of dictionaries. Each disctionary represents a day and contains a list of free quarters
    days = []
    current_day = start_time.date()
    while current_day <= end_time.date():
        day = {"date": current_day, "free_slots": list(range(0, 96))}
        days.append(day)
        current_day += datetime.timedelta(days=1)
    
    # Remove the quarters that are not free
    for event in events:
        start_day = event["start"].date()
        end_day = event["end"].date()
        start_quarter = time_to_quarter(event["start"].time())
        end_quarter = time_to_quarter(event["end"].time())

        if start_day == end_day:
            for day in days:
                if day["date"] == start_day:
                    day["free_slots"] = [quarter for quarter in day["free_slots"] if quarter < start_quarter or quarter >= end_quarter]
        else:
            for day in days:
                if day["date"] == start_day:
                    day["free_slots"] = [quarter for quarter in day["free_slots"] if quarter < start_quarter]
                elif day["date"] == end_day:
                    day["free_slots"] = [quarter for quarter in day["free_slots"] if quarter >= end_quarter]
                elif start_day < day["date"] < end_day:
                    day["free_slots"] = []
    return days


def get_available_slots_for_ticket(ticket):
    """Returns a list of weeks, which is containing a list of days, which is containing available slots for the ticket."""
    # Get all calendars of the user
    calendars = Calendar.objects.filter(assigned_user=ticket.assigned_user)
    # Get all events of all the calendars
    events = []
    for cal in calendars:
        events += caldav.get_all_caldav_events(cal.url, cal.username, cal.password)
    # Convert the first_available_date to a datetime object
    first_possible_datetime = datetime.datetime.combine(ticket.first_available_date, datetime.time(0, 0))
    if first_possible_datetime < datetime.datetime.now():
        first_possible_datetime = datetime.datetime.now() + datetime.timedelta(minutes=15)
    settings = booking.get_booking_settings_for_user(ticket.assigned_user)
    days = get_free_slots(events, first_possible_datetime, datetime.datetime.now() + datetime.timedelta(days=settings.maximum_future_booking_time))
    print_days_with_free_slots(days)
    duration = ticket.duration
    # Make sure that duration is in a 15 minute interval, e.g. 17 minutes will be extended to 30 minutes
    if duration.seconds % 900 != 0:
        duration = duration + datetime.timedelta(seconds=900 - duration.seconds % 900)
    # Get duration in quarters
    duration_in_quarters = duration.seconds // 900
    # Remove all days which are not in the future
    timezone = pytz.timezone("Europe/Berlin") 
    days = [day for day in days if day["date"] >= datetime.datetime.now(timezone).date()]
    
    earliest_booking_time = settings.earliest_booking_time
    latest_booking_end = settings.latest_booking_end
    
    # Remove all slots which are not in the time frame between earliest_booking_time and latest_booking_end
    for day in days:
        day["free_slots"] = [slot for slot in day["free_slots"] if quarter_to_time(slot) >= earliest_booking_time and quarter_to_time(slot) < latest_booking_end]
    
    for day in days:
        # Now generate a list of available slots.
        # Each available slot should respect the duration of the ticket and latest_booking_end
        # Also make sure that all free_slots are available for the duration of the ticket
        day["slots"] = []

        # Find all clusters of free slots we will sort out the short ones later
        available_clusters = []
        while len(day["free_slots"]) > 0:
            start = day["free_slots"].pop(0)
            end = start
            while end + 1 in day["free_slots"]:
                end += 1
                day["free_slots"].remove(end)
            available_clusters.append(range(start, end + 1))
        # Now let's sort out the clusters which are too short
        available_clusters = [cluster for cluster in available_clusters if len(cluster) >= duration_in_quarters]

        # Now lets create a list of available slots
        # For that we remove the amount of quarters of the duration from the end of the cluster
        for cluster in available_clusters:
            cluster = cluster[:-duration_in_quarters + 1]
            for slot in cluster:
                day["slots"].append(slot)

        # Now we should be finished with the slot finding
                
        # If there are more options than 5 we remove all slots which are either at :15, or :45
        if len(day["slots"]) > 5:
            day["slots"] = [slot for slot in day["slots"] if not is_quarter_15_or_45(slot)]

        # If there are more option than 10 we remove all slots which are at :30
        if len(day["slots"]) > 10:
            day["slots"] = [slot for slot in day["slots"] if not is_quarter_30(slot)]
                
        # Lets convert the slots to dicts with start, end 
        new_slots = []
        for slot in day["slots"]:
            new_slots.append({"start": quarter_to_time(slot), "end": quarter_to_time(slot + duration_in_quarters)})
        day["slots"] = new_slots

        # Generate a good looking title for the day in german
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
        day["title"] = day["date"].strftime("%A, %d.%m.%Y")
        # If day is today, add "Heute" to the title
        if day["date"] == datetime.datetime.now(timezone).date():
            day["title"] = "Heute, " + day["title"]
            # Remove all slots which are in the past (here our timezone is Berlin, so we can use the timezone directly)
            # We remove the slots here, because above we would have issues by comparing "different" timezones
            # We can't set everything to the real timezone, because apparently the database is not timezone aware
            day["slots"] = [slot for slot in day["slots"] if time_to_quarter(slot["start"]) > time_to_quarter((datetime.datetime.now(timezone) + datetime.timedelta(minutes=15)).time())]
        # If day is tomorrow, add "Morgen" to the title
        if day["date"] == datetime.datetime.now(timezone).date() + datetime.timedelta(days=1):
            day["title"] = "Morgen, " + day["title"]
    
    # Now generate a list of weeks
    # Make sure, the first week also has 7 days
    # If the first day is not a monday, add empty days to the beginning
    weeks = []
    current_week = []
    empty_day = {"date": None, "slots": [], "empty": True}
    for day in days:
        if not day["date"].weekday() == 0 and len(current_week) == 0:
            for i in range(day["date"].weekday()):
                current_week.append(empty_day)
        current_week.append(day)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []

    # If the last week is not full, add empty days to the end
    if len(current_week) > 0:
        for i in range(7 - len(current_week)):
            current_week.append(empty_day)
        weeks.append(current_week)

    # Now we check, which days are excluded by the user in the settings:
    if settings.sunday == False:
        for week in weeks:
            week.pop(6)
    if settings.saturday == False:
        for week in weeks:
            week.pop(5)
    if settings.friday == False:
        for week in weeks:
            week.pop(4)
    if settings.thursday == False:
        for week in weeks:
            week.pop(3)
    if settings.wednesday == False:
        for week in weeks:
            week.pop(2)
    if settings.tuesday == False:
        for week in weeks:
            week.pop(1)
    if settings.monday == False:
        for week in weeks:
            week.pop(0)

    # Now if a week is empty, we remove it
    weeks = [week for week in weeks if not all([day["date"] == None for day in week])]

    return weeks
            
    




def print_days_with_free_slots(days):
    all_slots = range(0, 96)
    for day in days:
        line = str(day["date"]) + ": "
        for slot in all_slots:
            if slot in day["free_slots"]:
                line += " "
            else:
                line += "#"
        print(line)


# events = caldav.get_all_caldav_events("https://caldav.fastmail.com/dav/calendars/username/username/", "username", "password")
# # Start: Today 00:00, End: in 7 days
# today_0_0 = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
# days = get_free_slots(events, today_0_0, today_0_0 + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999))
# print_days_with_free_slots(days)
        

def set_main_calendar_for_user(user, calendar):
    """Sets the main calendar for a user. If the user already has a main calendar, all other calendars are set to not main calendar."""
    all_calendars = Calendar.objects.filter(assigned_user=user)
    for cal in all_calendars:
        if cal == calendar:
            cal.main_calendar = True
        else:
            cal.main_calendar = False
        cal.save()


def get_main_calendar_for_user(user):
    """Returns the main calendar for a user. Otherwise None."""
    all_calendars = Calendar.objects.filter(assigned_user=user)
    for cal in all_calendars:
        if cal.main_calendar:
            return cal
    return None


def generate_guid():
    return str(uuid.uuid4())


def remove_booking(ticket_guid):
    """Removes the booking from the calendar."""
    ticket = Ticket.objects.get(guid=ticket_guid)
    calendar = get_main_calendar_for_user(ticket.assigned_user)
    caldav.delete_caldav_event(ticket.caldav_event_uid, calendar.url, calendar.username, calendar.password)
    ticket.current_date = None
    ticket.caldav_event_uid = None
    ticket.save()    


def book_ticket(ticket_guid):
    """Books the ticket in the calendar."""
    ticket = Ticket.objects.get(guid=ticket_guid)
    calendar = get_main_calendar_for_user(ticket.assigned_user)
    start = ticket.current_date
    end = ticket.current_date + ticket.duration
    caldav_uid = generate_guid()
    jitsi_link = booking.get_jitsi_link_for_ticket(ticket)
    caldav.create_caldav_event(start, end, caldav_uid, ticket.name, calendar.url, calendar.username, calendar.password, jitsi_link)
    ticket.caldav_event_uid = caldav_uid
    ticket.save()


def get_ical_string_for_ticket(ticket_guid):
    """Returns the ical string for the ticket."""
    ticket = Ticket.objects.get(guid=ticket_guid)
    start = ticket.current_date
    end = ticket.current_date + ticket.duration
    summary = booking.get_ticket_description_for_customer(ticket)
    jitsi_link = booking.get_jitsi_link_for_ticket(ticket)
    return caldav.get_ical_string_for_event(start, end, summary, jitsi_link)


# DEPRECATED
# Also doesn't work reliable in practice
# def is_slot_available(ticket_guid, date, start_time):
#     ticket = Ticket.objects.get(guid=ticket_guid)
#     weeks = get_available_slots_for_ticket(ticket)
#     for week in weeks:
#         for day in week:
#             if day["date"] == None:
#                 continue
#             if day["date"].strftime("%Y-%m-%d").strip() == date.strftime("%Y-%m-%d").strip():
#                 for slot in day["slots"]:
#                     if slot["start"].strftime("%H:%M").strip() == start_time.strftime("%H:%M").strip():
#                         return True
#             return False
        
#     return False
    