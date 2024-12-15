# Example: "Berlin": "Europe/Berlin",
# Now with all timezones and cities
common_timezones = {
    "Berlin": "Europe/Berlin",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Los Angeles": "America/Los_Angeles",
    "Chicago": "America/Chicago",
    "Denver": "America/Denver",
    "Phoenix": "America/Phoenix",
    "Anchorage": "America/Anchorage",
    "Honolulu": "Pacific/Honolulu",
    "Sydney": "Australia/Sydney",
    "Tokyo": "Asia/Tokyo",
    "Shanghai": "Asia/Shanghai",
    "New Delhi": "Asia/Kolkata",
    "Dubai": "Asia/Dubai",
    "Moscow": "Europe/Moscow",
    "Paris": "Europe/Paris",
    "Rome": "Europe/Rome",
    "Madrid": "Europe/Madrid",
    "Amsterdam": "Europe/Amsterdam",
    "Stockholm": "Europe/Stockholm",
    "Athens": "Europe/Athens",
    "Istanbul": "Europe/Istanbul",
    "Cairo": "Africa/Cairo",
    "Cape Town": "Africa/Johannesburg",
    "Rio de Janeiro": "America/Sao_Paulo",
    "Buenos Aires": "America/Argentina/Buenos_Aires",
    "Mexico City": "America/Mexico_City",
    "Vancouver": "America/Vancouver",
    "Toronto": "America/Toronto",
    "Montreal": "America/Montreal",
    "Calgary": "America/Edmonton",
    "Halifax": "America/Halifax",
    "Sao Paulo": "America/Sao_Paulo",
    "Bogota": "America/Bogota",
    "Lima": "America/Lima",
    "Caracas": "America/Caracas",
    "Santiago": "America/Santiago",
    "Auckland": "Pacific/Auckland",
    "Wellington": "Pacific/Auckland",
    "Melbourne": "Australia/Melbourne",
    "Brisbane": "Australia/Brisbane",
    "Perth": "Australia/Perth",
    "Adelaide": "Australia/Adelaide",
    "Darwin": "Australia/Darwin",
    "Hobart": "Australia/Hobart",
    "Dublin": "Europe/Dublin",
    "Bangkok": "Asia/Bangkok",
    "Jakarta": "Asia/Jakarta",
    "Manila": "Asia/Manila",
    "Seoul": "Asia/Seoul",
    "Hanoi": "Asia/Ho_Chi_Minh",
    "CET": "Europe/Paris",
    "CST": "America/Chicago",
    "EST": "America/New_York",
    "GMT": "Europe/London",
    "PST": "America/Los_Angeles",
    "AEST": "Australia/Sydney",
    "UTC": "UTC",
}

common_timezones_array_of_dicts = []
for city, tz in common_timezones.items():
    common_timezones_array_of_dicts.append({"city": city, "tz": tz})