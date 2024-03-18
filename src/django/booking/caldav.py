import httplib2
import base64
import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import unquote

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

def get_events_from_response(response : str):
    lines = response.split("\n")
    events = []
    # Find first event
    while not lines[0].startswith("BEGIN:VEVENT"):
        lines.pop(0)
    # Now we are at the first event
    while(len(lines) > 0):
        line = lines.pop(0)
        if line.startswith("BEGIN:VEVENT"):
            event = {}
            while not line.startswith("END:VEVENT"):
                if line.startswith("DTSTART"):
                    start = line.split(":")[1]
                    start = start.split("Z")[0]
                    start = start.strip()
                    if "T" in start:
                        event["start"] = datetime.datetime.strptime(start, "%Y%m%dT%H%M%S")
                    else:
                        event["start"] = datetime.datetime.strptime(start, "%Y%m%d")
                elif line.startswith("DTEND"):
                    end = line.split(":")[1]
                    end = end.split("Z")[0]
                    end = end.strip()
                    if "T" in end:
                        event["end"] = datetime.datetime.strptime(end, "%Y%m%dT%H%M%S")
                    else:
                        event["end"] = datetime.datetime.strptime(end, "%Y%m%d")
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
                    if len(exdate) == 8:
                        event["exdate"].append(datetime.datetime.strptime(exdate, "%Y%m%d"))
                    elif len(exdate) == 15:
                        event["exdate"].append(datetime.datetime.strptime(exdate, "%Y%m%dT%H%M%S"))
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


    # Parse the rrules and generate every occurence of the event (maximum 1 year in the future)
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
    return events

events_cache = {}

# If the cached object is older than 1 minute, we return None and remove the object from the cache
def get_cached_events(caldav_adress, username: str=""):
    cache_key = caldav_adress + username
    if cache_key in events_cache:
        if (datetime.datetime.now() - events_cache[cache_key]["time"]).seconds < 60:
            return events_cache[cache_key]["events"]
        else:
            del events_cache[cache_key]
    return None

def cache_events(caldav_adress, username: str="", events: list=[]):
    cache_key = caldav_adress + username
    events_cache[cache_key] = {"time": datetime.datetime.now(), "events": events}

def get_all_caldav_events(caldav_adress, username: str=None, password: str=None):
    if get_cached_events(caldav_adress, username):
        return get_cached_events(caldav_adress, username)
    http = httplib2.Http()

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
            return []
   
    # Startdate: one week ago, format YYYY-MM-DD
    start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d")
    # Enddate: four weeks from now, format YYYY-MM-DD
    end_date = (datetime.datetime.now() + datetime.timedelta(weeks=4)).strftime("%Y%m%d")



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
        # Write content to file
        with open("calendar.txt", "w") as file:
            file.write(content)
        events = get_events_from_response(content)
        cache_events(caldav_adress, username, events)
        return events
    else:
        print(f"Error retrieving events: {response.status}")
        return []


def create_caldav_event(start: datetime.datetime, end: datetime.datetime, uid: str,  summary: str, caldav_address: str, username: str=None, password: str=None):
    http = httplib2.Http()
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
DTSTART:{start.strftime("%Y%m%dT%H%M%S")}
DTEND:{end.strftime("%Y%m%dT%H%M%S")}
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
    response, content = http.request(
        caldav_address, "DELETE", headers=headers
    )
    if response.status == 204:
        return True
    else:
        print(f"Error deleting event: {response.status}")
        print(content)
        return False
    

# Make sure that the the user can't click on "accept" or "decline" in the mail client
def get_ical_string_for_event(start: datetime.datetime, end: datetime.datetime, summary: str, location: str = ""):
    return f"""BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:{summary}
LOCATION:{location}
DTSTART:{start.strftime("%Y%m%dT%H%M%S")}
DTEND:{end.strftime("%Y%m%dT%H%M%S")}
END:VEVENT
END:VCALENDAR
"""