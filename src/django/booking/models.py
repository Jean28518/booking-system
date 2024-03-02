from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Calendars
class Calendar(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name