import django.forms as forms
from django.utils.translation import gettext_lazy as _

from .models import Calendar, Ticket, BookingSettings


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['name', 'url', 'username', 'password', 'main_calendar']
        labels = {
            'name': _('Name'),
            'url': _('CalDAV URL'),
            'username': _('Username'),
            'password': _('Password'),
            'main_calendar': _('Main calendar'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.TextInput(attrs={'class': 'form-control'}),
            'main_calendar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketForm(forms.ModelForm):
    ticket_customer_link = forms.CharField(label=_('Customer Link'), widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = Ticket
        fields = ['name', 'first_available_date', 'duration', 'expiry', 'generate_jitsi_link']
        labels = {
            'name': _('Name'),
            'first_available_date': _('First available date'),
            'duration': _('Duration (Hours)'),
            'expiry': _('Expiry date'),
            'generate_jitsi_link': _('Generate jitsi link'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_available_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'aria-label': "Date"}, format='%Y-%m-%d'),
            'duration': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'aria-label': "Time"}),
            'expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'aria-label': "Date"}, format='%Y-%m-%d'),
            'generate_jitsi_link': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BookingSettingsForm(forms.ModelForm):
    class Meta:
        model = BookingSettings
        fields = ['earliest_booking_time', 'latest_booking_end', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'jitsi_server', 'maximum_future_booking_time']
        labels = {
            'earliest_booking_time': _('Earliest booking time'),
            'latest_booking_end': _('Latest booking end (when do you finish work?)'),
            'monday': _('Appointments on') + ' ' + _('Monday'),
            'tuesday': _('Appointments on') + ' ' + _('Tuesday'),
            'wednesday': _('Appointments on') + ' ' + _('Wednesday'),
            'thursday': _('Appointments on') + ' ' + _('Thursday'),
            'friday': _('Appointments on') + ' ' + _('Friday'),
            'saturday': _('Appointments on') + ' ' + _('Saturday'),
            'sunday': _('Appointments on') + ' ' + _('Sunday'),
            'jitsi_server': _('Jitsi server base URL'),
            'maximum_future_booking_time': _('Maximum future booking time (in days)'),
        }
        widgets = {
            'earliest_booking_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'aria-label': "Time"}),
            'latest_booking_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'aria-label': "Time"}),
            'monday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tuesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wednesday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'thursday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'friday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saturday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sunday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'jitsi_server': forms.URLInput(attrs={'class': 'form-control'}),
            'maximum_future_booking_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
