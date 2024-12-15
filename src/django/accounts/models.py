from django.db import models

from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(default='', upload_to='profile_pictures')
    phone = models.CharField(max_length=20, default='')
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return f'{self.user.username} Profile'