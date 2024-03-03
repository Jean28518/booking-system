import django.forms as forms

from .models import Calendar, Ticket

class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['name', 'url', 'username', 'password', 'main_calendar']
        labels = {
            'name': 'Name',
            'url': 'CalDAV-URL',
            'username': 'Username',
            'password': 'Password',
            'main_calendar': 'Main Calendar',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'main_calendar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['name', 'first_available_date', 'duration', 'expiry', 'generate_jitsi_link']
        labels = {
            'name': 'Name',
            'first_available_date': 'Erstes verfügbares Datum',
            'duration': 'Dauer (Minuten)',
            'expiry': 'Ablaufdatum',
            'generate_jitsi_link': 'Generate Jitsi Link',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_available_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'aria-label': "Date"}),
            'duration': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'aria-label': "Time"}),
            'expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'aria-label': "Date"}),
            'generate_jitsi_link': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
