import datetime
# import caldav
import booking.caldav as caldav

def time_to_quarter(time):
    return time.hour * 4 + time.minute // 15


def quarter_to_time(quarter):
    return datetime.time(quarter // 4, (quarter % 4) * 15)


def get_free_slots(events, start_time: datetime.datetime, end_time: datetime.datetime):
    """Returns a list of days, which is containing a list of free quarters for each day."""

    # for event in events:
    #     if "Schwimmen" in event["summary"]:
    #         print(event)

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


events = caldav.get_all_caldav_events("https://caldav.fastmail.com/dav/calendars/username/username/", "username", "password")
# Start: Today 00:00, End: in 7 days
today_0_0 = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
days = get_free_slots(events, today_0_0, today_0_0 + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999))
print_days_with_free_slots(days)