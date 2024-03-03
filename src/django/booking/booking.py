from .models import BookingSettings

def get_booking_settings_for_user(user):
    try:
        return BookingSettings.objects.get(assigned_user=user)
    except BookingSettings.DoesNotExist:
        return BookingSettings(assigned_user=user)