from django.db import models
from django.contrib.auth.models import User
import datetime

# Create your models here.

# Calendars
class Calendar(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=200)
    username = models.CharField(max_length=200, null=True, blank=True)
    password = models.CharField(max_length=200, null=True, blank=True)
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE)
    main_calendar = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Ticket(models.Model):
    name = models.CharField(max_length=200)
    first_available_date = models.DateField()
    duration = models.DurationField()
    expiry = models.DateField()
    generate_jitsi_link = models.BooleanField(default=False)
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_date = models.DateTimeField(null=True, blank=True)
    email_of_customer = models.EmailField(max_length=200, null=True, blank=True)
    caldav_event_uid = models.CharField(max_length=200, null=True, blank=True)
    guid = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class BookingSettings(models.Model):
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE)
    earliest_booking_time = models.TimeField(default=datetime.time(8, 0))
    latest_booking_end = models.TimeField(default=datetime.time(18, 0))
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    jitsi_server = models.URLField(max_length=200, null=True, blank=True)
    maximum_future_booking_time = models.IntegerField(default=42)