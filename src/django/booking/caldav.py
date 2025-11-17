import httplib2
import base64
import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import unquote
from booking.timezones import common_timezones_array_of_dicts, convert_time_from_local_to_utc
import pytz
import cfg.cfg as cfg
import os
import json

def day_to_number(day: str):
    if day == "MO":
        return 0
    if day == "TU":
        return 1
    if day == "WE":
        return 2
    if day == "TH":
        return 3
    if day == "FR":
        return 4
    if day == "SA":
        return 5
    if day == "SU":
        return 6
    return -1

def _parse_datetime(datetimes: str):
    datetimes = datetimes.strip()
    datetimes = datetimes.split("Z")[0]
    if "T" in datetimes:
        try:
            return datetime.datetime.strptime(datetimes, "%Y%m%dT%H%M%S")
        except:
            datetimes = datetimes.split("T")[0]
            return datetime.datetime.strptime(datetimes, "%Y%m%d")
    elif len(datetimes) == 8:
        return datetime.datetime.strptime(datetimes, "%Y%m%d")
    else:
        print("Could not parse datetime: " + str(datetimes))
        return None
    
def get_events_from_response(response : str):
    """Get them all converted to utc"""
    lines = response.split("\n")
    events = []
    # Find first event
    if len(lines) == 0:
        return []
    while not lines[0].startswith("BEGIN:VEVENT"):
        lines.pop(0)
        if len(lines) == 0:
            return []
    # Now we are at the first event
    while(len(lines) > 0):
        line = lines.pop(0)
        if line.startswith("BEGIN:VEVENT"):
            event = {}
            while not line.startswith("END:VEVENT"):
                if "TZID" in line:
                    # Try every timezone:
                    for tz in common_timezones_array_of_dicts:
                        if tz["city"] in line or tz["tz"] in line:
                            event["tz"] = tz["tz"]
                            break
                if line.startswith("DTSTART"):
                    start = line.split(":")[1]
                    event["start"] = _parse_datetime(start)
                elif line.startswith("DTEND"):
                    end = line.split(":")[1]
                    event["end"] = _parse_datetime(end)
                elif line.startswith("SUMMARY"):
                    event["summary"] = line.split(":")[1]
                elif line.startswith("RRULE"):
                    event["rrule"] = line.split(":")[1]
                elif line.startswith("UID:"):
                    event["uid"] = line.split(":")[1]
                elif line.startswith("RECURRENCE-ID"):
                    recurrence_id = line.split(":")[1]
                    recurrence_id = recurrence_id.split("Z")[0].strip()
                    if len(recurrence_id) == 8:
                        event["recurrence_id"] = datetime.datetime.strptime(recurrence_id, "%Y%m%d")
                    elif len(recurrence_id) == 15:
                        event["recurrence_id"] = datetime.datetime.strptime(recurrence_id, "%Y%m%dT%H%M%S")
                elif line.startswith("EXDATE"):
                    exdate = line.split(":")[1]
                    exdate = exdate.split("Z")[0].strip()
                    if not event.get("exdate", None):
                        event["exdate"] = []
                    exdate_entry = _parse_datetime(exdate)
                    if exdate_entry:
                        event["exdate"].append(exdate_entry)
                    
                # elif line.startswith("DESCRIPTION"):
                #     event["description"] = line.split(":")[1]
                #     # Description can be multiline
                # Also get if it is marked as busy or free
                elif line.startswith("TRANSP"):
                    transp = line.split(":")[1]
                    if transp == "OPAQUE":
                        event["busy"] = True
                    else:
                        event["busy"] = False
                line = lines.pop(0)
            # Ensure that the event is cointaining all necessary information
            if not "busy" in event:
                event["busy"] = True
            if not "end" in event and "start" in event:
                event["end"] = event["start"] + datetime.timedelta(hours=1)
            if not "summary" in event:
                event["summary"] = ""

            if "start" in event and "end" in event and "summary" in event and "busy" in event:
                events.append(event)
            else:
                print("Event is missing information: " + str(event))


    # Parse the rules and generate every occurence of the event (maximum 1 year in the future)
    for event in events:
        if "rrule" in event:
            rrule = event["rrule"]
            rrule = rrule.split(";")
            freq = rrule[0].split("=")[1]
            interval = 1
            count = 0
            until = datetime.datetime.now() + datetime.timedelta(days=365)
            bydays = []
            bymonthdays = []
            for r in rrule:
                if r.startswith("INTERVAL"):
                    interval = int(r.split("=")[1])
                if r.startswith("COUNT"):
                    count = int(r.split("=")[1])
                    until = event["start"] + datetime.timedelta(days=count*interval)
                if r.startswith("UNTIL"):
                    until = r.split("=")[1]
                    until = until.split("T")[0]
                    until = datetime.datetime.strptime(until, "%Y%m%d")
                if r.startswith("BYDAY"):
                    bydays = r.split("=")[1].split(",")
                if r.startswith("BYMONTHDAY"):
                    bymonthdays = r.split("=")[1].split(",")
            if until > datetime.datetime.now() + datetime.timedelta(days=365):
                until = datetime.datetime.now() + datetime.timedelta(days=365)
            
            # EASY HANDLING
            if bydays == [] and bymonthdays == []:
                if freq == "DAILY":
                    current = event["start"]
                    while current < until:
                        current = current + datetime.timedelta(days=interval)
                        new_event = event.copy()
                        new_event["start"] = current
                        new_event["end"] = current + (event["end"] - event["start"])
                        del new_event["rrule"]
                        events.append(new_event)
                if freq == "WEEKLY":
                    current = event["start"]
                    while current < until:
                        current = current + datetime.timedelta(weeks=interval)
                        new_event = event.copy()
                        new_event["start"] = current
                        new_event["end"] = current + (event["end"] - event["start"])
                        del new_event["rrule"]
                        events.append(new_event)
                if freq == "MONTHLY":
                    current = event["start"]
                    while current < until:
                        current = current + relativedelta(months=interval)
                        new_event = event.copy()
                        new_event["start"] = current
                        new_event["end"] = current + (event["end"] - event["start"])
                        del new_event["rrule"]
                        events.append(new_event)
                if freq == "YEARLY":
                    current = event["start"]
                    while current < until:
                        current = current + relativedelta(years=interval)
                        new_event = event.copy()
                        new_event["start"] = current
                        new_event["end"] = current + (event["end"] - event["start"])
                        del new_event["rrule"]
                        events.append(new_event)

            # BYDAY HANDLING
            elif bydays != []:
                if count == 0:
                    count = 1000000
                occurence_count = 0
                current_date = event["start"]
                while current_date < until:
                    # print("EVENT: " + str(event))
                    # print("BYDAYS: " + str(bydays))
                    if occurence_count >= count:
                        break

                    # Calculate the next earliest occurence of the event, if we are finished with the current byday cycle
                    if occurence_count % len(bydays) == 0:
                        earliest_occurence = current_date
                        if freq == "DAILY":
                            earliest_occurence = current_date + datetime.timedelta(days=interval)
                        # To the earliest occurence of the event in the next week
                        if freq == "WEEKLY":
                            earliest_occurence = current_date + datetime.timedelta(weeks=interval)
                            # print("EARLIEST WEEKLY OCCURENCE: " + str(earliest_occurence))
                            # Set the earliest_occurence to monday:
                            earliest_occurence = earliest_occurence - datetime.timedelta(days=current_date.weekday())
                            # print("EARLIEST WEEKLY OCCURENCE: " + str(earliest_occurence))
                        # To the earliest occurence of the event in the next month
                        if freq == "MONTHLY":
                            # print("!176")
                            earliest_occurence = current_date + relativedelta(months=interval)
                            # print("EARLIEST MONTHLY OCCURENCE: " + str(earliest_occurence))
                            # Set the current date to the first day of the month
                            earliest_occurence = earliest_occurence.replace(day=1)
                            # print("FIRST DAY OF MONTH: " + str(earliest_occurence))
                        # To the earliest occurence of the event in the next year
                        if freq == "YEARLY":
                            # We don't support yearly events with ByDay at the time.
                            break
                        
                        # Now parse byday to get the next occurence of the event
                        # Some Possible values are: MO, 1MO, 3SU, -1MO, -2TU
                        occurences = []
                        for byday in bydays:
                            if byday[0] == "-":
                                    print("We don't support negative by day numbers at the moment")
                                    count += 1
                                    break
                            if occurence_count >= count:
                                break

                            if freq == "DAILY":
                                # Calculate the next day
                                occurences.append(earliest_occurence + datetime.timedelta(days=day_to_number(byday)))
                            if freq == "WEEKLY":
                                # Calculate the next day
                                occurences.append(earliest_occurence + datetime.timedelta(days=day_to_number(byday)))
                            if freq == "MONTHLY":
                                # Get the number that we know in which week of the month we are looking for
                                week_of_month = 0
                                if byday[0].isdigit():
                                    week_of_month = int(byday[0])-1
                                    day = byday[1:]
                                else:
                                    day = byday
                                # Get the week for which we are looking for
                                week_begin = earliest_occurence + datetime.timedelta(weeks=week_of_month)
                                # print("WEEK: " + str(week_begin))
                                # print("week_begin.weekday()" + str(week_begin.weekday()))
                                if week_begin.weekday() > day_to_number(day):
                                    week_begin = week_begin + datetime.timedelta(days=(7-week_begin.weekday()))
                                # Get the monday of the week
                                week_begin = week_begin - datetime.timedelta(days=(week_begin.weekday()))
                                # print("MONDAY: " + str(week_begin))
                                # Add the occurence
                                occurences.append(week_begin + datetime.timedelta(days=day_to_number(day)))
                                
                        # print("OCCURENCES: " + str(occurences))
                        for occurence in occurences:
                            if occurence_count < count:
                                new_event = event.copy()
                                new_event["start"] = occurence
                                current_date = occurence
                                new_event["end"] = occurence + (event["end"] - event["start"])
                                del new_event["rrule"]
                                events.append(new_event)
                                occurence_count += 1

            # BYMONTHDAY HANDLING
            # TODO



    # Now we need to remove all "double" events, which are doubled because of the rrule and the reccurence id :)
    # So if we have a reccurence id set, this is the right event and we can remove the other event with the same uid and the same start date which is the content of the reccurence id
    events_to_remove = []
    for event in events:
        if event.get("recurrence_id", None):
            for e in events:
                if e["uid"] == event["uid"] and e["start"] == event["recurrence_id"]:
                    events_to_remove.append(e)
                    # print("REMOVED EVENT: " + str(e))
                    break

        # Now we need to remove all events, which are removed by the exdate :)
        # And because exdate is also saved in the generated reccurence events, we can simply remove all events which are in the exdate list
        if event.get("exdate", None):
            for exdate in event["exdate"]:
                if exdate == event["start"]:
                    events_to_remove.append(event)
                    # print("REMOVED EVENT: " + str(event))

    for event in events_to_remove:
        events.remove(event)

    # Convert all events to UTC
    for event in events:
        if "tz" in event:
            event["start"] = convert_time_from_local_to_utc(event["start"], event["tz"])
            event["end"] = convert_time_from_local_to_utc(event["end"], event["tz"])
            del event["tz"]
        else:
            # event["start"] = convert_time_from_local_to_utc(event["start"], "UTC")
            # event["end"] = convert_time_from_local_to_utc(event["end"], "UTC")
            # Because some appointments do not have a timezone set at my caldav server, we assume it to Berlin.
            # In the future we should change this to UTC :)
            event["start"] = convert_time_from_local_to_utc(event["start"], "Europe/Berlin")
            event["end"] = convert_time_from_local_to_utc(event["end"], "Europe/Berlin")

    return events

events_cache = {}

def _serialize_events_obj(obj):
    """
    Custom JSON serializer for datetime objects.
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    # Let the JSON encoder raise a TypeError for other unsupported types.
    # This avoids the 'str(obj)' bug.
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def unserialize_events_obj(dct):
    """
    Custom JSON object_hook to deserialize datetime strings.
    Note: This naive implementation may incorrectly parse strings that look like datetimes but aren't intended to be.
    e.g., {"summary": "2025-01-01T00:00:00"} -> {"summary": datetime.datetime(...)}
    A better long-term solution is to check keys or use a custom type format.
    """
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                # Attempt to parse *only* strings
                dct[key] = datetime.datetime.fromisoformat(value)
            except (ValueError, TypeError):
                # ValueError: not an ISO string
                # TypeError: e.g., fromisoformat() received a non-string
                pass  # Keep the original string value
    return dct

def get_cached_events(caldav_adress, username: str="", cache_duration_seconds: int = 300):
    filename = generate_ics_filename(caldav_adress) + "_cache.json"
    
    if not os.path.exists(filename):
        return None

    try:
        # 1. Check modification time FIRST
        cache_mtime = os.path.getmtime(filename)
        cache_time = datetime.datetime.fromtimestamp(cache_mtime)
        
        # 2. Use .total_seconds() for the check
        if (datetime.datetime.now() - cache_time).total_seconds() >= cache_duration_seconds:
            # Cache is expired, remove it and return
            os.remove(filename)
            return None
            
        # 3. Cache is fresh, *now* we read and parse it
        with open(filename, "r") as file:
            data = json.load(file, object_hook=unserialize_events_obj)
            return data.get("events") # Use .get() for safety

    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        # Catch specific errors.
        # If file is corrupt, missing (race condition), or unreadable,
        # delete it (if it still exists) and return None.
        if os.path.exists(filename):
            os.remove(filename)
        return None

def cache_events(caldav_adress, username: str="", events: list=[]):
    filename = generate_ics_filename(caldav_adress) + "_cache.json"
    data_to_cache = {"events": events}
    
    try:
        with open(filename, "w") as file:
            # 4. Use json.dump() (no 's') to write to the file
            json.dump(data_to_cache, file, default=_serialize_events_obj)
    except (PermissionError, OSError) as e:
        # Handle cases where we can't write the cache file
        print(f"Warning: Could not write cache file {filename}. Error: {e}")

def clear_caldav_cache_for_user(user):
    """Clears the caldav cache for all calendars of the given user."""
    from booking.models import Calendar
    calendars = Calendar.objects.filter(user=user)
    for calendar in calendars:
        filename = generate_ics_filename(calendar.url) + "_cache.json"
        if os.path.exists(filename):
            os.remove(filename)
        ics_filename = generate_ics_filename(calendar.url)
        if os.path.exists(ics_filename):
            os.remove(ics_filename)


def generate_ics_filename(caldav_adress: str):
    caldav_adress_filename = "/tmp/" + caldav_adress.replace("/", "_").replace(":", "_") 
    return f"{caldav_adress_filename}.ics"


# Called every 5 minutes to download the ics file and cache it (called by calendar.retrieve_all_caldav_calendars_for_all_users)
def download_ics_file(caldav_adress, username: str=None, password: str=None):
    if username is None:
        username = ""
    if password is None:
        password = ""
    if get_cached_events(caldav_adress, username):
        return get_cached_events(caldav_adress, username)
    http = httplib2.Http()
    if cfg.get_value("skip_ssl_check", False):
        http.disable_ssl_certificate_validation = True

    if caldav_adress.endswith(".ics"):
        headers = {
        }
        if username and password:
            # Add Basic Authentication header
            headers["Authorization"] = "Basic " + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        response, ics_content = http.request(caldav_adress, "GET", headers=headers)
        if response.status == 200:
            return get_events_from_response(ics_content.decode("utf-8"))
        else:
            print(f"Error retrieving events: {response.status}")
   
    # Build XML body
    xml_body = f"""
    <c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
        <d:prop>
            <d:getetag />
            <c:calendar-data />
        </d:prop>
        <c:filter>
          <c:comp-filter name="VCALENDAR" />
        </c:filter>
    </c:calendar-query>
    """ 

    # Set headers
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml; charset=utf-8",
        "Prefer": "return-minimal",
    }

    if username and password:
        # Add Basic Authentication header
        headers["Authorization"] = "Basic " + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")

    # Send REPORT request
    response, content = http.request(
        caldav_adress, "REPORT", body=xml_body, headers=headers
    )

    # Check for successful response
    if response.status == 207:
        content = content.decode("utf-8")
        caldav_adress_filename = generate_ics_filename(caldav_adress)
        with open(caldav_adress_filename, "w") as file:
            file.write(content)
    else:
        print(f"Error retrieving .ics file: {response.status}")
  

# Loads all events from the cached ics file or downloads it if not present
def get_all_caldav_events(caldav_adress, username: str=None, password: str=None):
    ics_filename = generate_ics_filename(caldav_adress)
    if not os.path.exists(ics_filename):
        download_ics_file(caldav_adress, username, password)

    if os.path.exists(ics_filename):
        with open(ics_filename, "r") as file:
            content = file.read()  
    else:
        print("ICS file does not exist: " + ics_filename)
        return []
    
    events = get_events_from_response(content)
    cache_events(caldav_adress, username, events)
    return events


def create_caldav_event(start: datetime.datetime, end: datetime.datetime, uid: str,  summary: str, caldav_address: str, username: str=None, password: str=None, location: str = ""):
    http = httplib2.Http()
    if cfg.get_value("skip_ssl_check", False):
        http.disable_ssl_certificate_validation = True

    summary = summary.replace("€", "EUR")

    headers = {
        "Content-Type": "text/calendar",
    }
    if not caldav_address.endswith(".ics"):
        if not caldav_address.endswith("/"):
            caldav_address += "/"
        caldav_address += f"{uid}.ics"

    if username and password:
        # Add Basic Authentication header
        headers["Authorization"] = "Basic " + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    event = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:{uid}
SUMMARY:{summary}
DTSTART;TZID=UTC:{start.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID=UTC:{end.strftime("%Y%m%dT%H%M%S")}
LOCATION:{location}
TZID:UTC
END:VEVENT
END:VCALENDAR
"""

    response, content = http.request(
        caldav_address, "PUT", body=event, headers=headers
    )
    if response.status == 201:
        return True
    else:
        print(f"Error creating event: {response.status}")
        print(content)
        return False
    
def delete_caldav_event(uid: str, caldav_address: str, username: str=None, password: str=None):
    http = httplib2.Http()
    if cfg.get_value("skip_ssl_check", False):
        http.disable_ssl_certificate_validation = True
    headers = {
        "Content-Type": "text/calendar",
    }
    if not caldav_address.endswith(".ics"):
        if not caldav_address.endswith("/"):
            caldav_address += "/"
        caldav_address += f"{uid}.ics"

    if username and password:
        # Add Basic Authentication header
        headers["Authorization"] = "Basic " + base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")

    # Let's try to delete multiple events, because sometimes some calendars are having multiple events of this ticket.
    deletion_success = False
    while True:
        response, content = http.request(
            caldav_address, "DELETE", headers=headers
        )
        if response.status == 204:
            deletion_success = True
        else:
            break
    if deletion_success:
        return True
    else:
        print(f"Error deleting event: {response.status}")
        print(content)
        return False
    

# Make sure that the the user can't click on "accept" or "decline" in the mail client
def get_ical_string_for_event(start: datetime.datetime, end: datetime.datetime, summary: str, location: str = "", description: str = ""):
    return f"""BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:{summary}
LOCATION:{location}
DESCRIPTION:{description}
DTSTART;TZID=UTC:{start.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID=UTC:{end.strftime("%Y%m%dT%H%M%S")}
TZID:UTC
BEGIN:VALARM
TRIGGER:-PT5M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
END:VCALENDAR
"""