from django.db import models
from django.contrib.auth.models import User

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

