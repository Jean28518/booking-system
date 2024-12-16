import pytz
from datetime import datetime


# Example: "Berlin": "Europe/Berlin",
# Now with all timezones and cities
common_timezones = {
    "Adelaide": "Australia/Adelaide",
    "Amsterdam": "Europe/Amsterdam",
    "Anchorage": "America/Anchorage",
    "Auckland": "Pacific/Auckland",
    "Athens": "Europe/Athens",
    "Bangkok": "Asia/Bangkok",
    "Beijing": "Asia/Shanghai",
    "Berlin": "Europe/Berlin",
    "Bogota": "America/Bogota",
    "Brisbane": "Australia/Brisbane",
    "Buenos Aires": "America/Argentina/Buenos_Aires",
    "Cairo": "Africa/Cairo",
    "Calgary": "America/Edmonton",
    "Cape Town": "Africa/Johannesburg",
    "Caracas": "America/Caracas",
    "Chicago": "America/Chicago",
    "CST": "America/Chicago",
    "Denver": "America/Denver",
    "Dubai": "Asia/Dubai",
    "Dublin": "Europe/Dublin",
    "EST": "America/New_York",
    "GMT": "Europe/London",
    "Halifax": "America/Halifax",
    "Hanoi": "Asia/Ho_Chi_Minh",
    "Hobart": "Australia/Hobart",
    "Honolulu": "Pacific/Honolulu",
    "Istanbul": "Europe/Istanbul",
    "Jakarta": "Asia/Jakarta",
    "London": "Europe/London",
    "Los Angeles": "America/Los_Angeles",
    "Madrid": "Europe/Madrid",
    "Manila": "Asia/Manila",
    "Melbourne": "Australia/Melbourne",
    "Mexico City": "America/Mexico_City",
    "Montreal": "America/Montreal",
    "Moscow": "Europe/Moscow",
    "New Delhi": "Asia/Kolkata",
    "New York": "America/New_York",
    "Paris": "Europe/Paris",
    "Perth": "Australia/Perth",
    "Phoenix": "America/Phoenix",
    "PST": "America/Los_Angeles",
    "Rio de Janeiro": "America/Sao_Paulo",
    "Rome": "Europe/Rome",
    "Santiago": "America/Santiago",
    "Sao Paulo": "America/Sao_Paulo",
    "Seoul": "Asia/Seoul",
    "Shanghai": "Asia/Shanghai",
    "Stockholm": "Europe/Stockholm",
    "Sydney": "Australia/Sydney",
    "Tokyo": "Asia/Tokyo",
    "Toronto": "America/Toronto",
    "UTC": "UTC",
    "Vancouver": "America/Vancouver",
    "Wellington": "Pacific/Auckland",
}

common_timezones_array_of_dicts = []
for city, tz in common_timezones.items():
    common_timezones_array_of_dicts.append({"city": city, "tz": tz})


def convert_time_from_local_to_local(
    time: datetime, from_tz: str, to_tz: str
):
    from_tz = pytz.timezone(from_tz)
    to_tz = pytz.timezone(to_tz)
    time = from_tz.localize(time)
    time = time.astimezone(to_tz)
    return time

def convert_time_from_local_to_utc(time: datetime, from_tz):
    if to_tz == None:
        to_tz = "UTC"
    if not type(from_tz) == str:
        from_tz = from_tz.zone
    from_tz = pytz.timezone(from_tz)
    time = from_tz.localize(time)
    time = time.astimezone(pytz.utc)    
    return time


def convert_time_from_utc_to_local(time: datetime, to_tz):
    if to_tz == None:
        to_tz = "UTC"
    if not type(to_tz) == str:
        to_tz = to_tz.zone
    to_tz = pytz.timezone(to_tz)
    time = time.astimezone(to_tz)
    return time

def get_timezone_of_string(timezone: str):
    return pytz.timezone(timezone)