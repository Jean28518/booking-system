import django.forms as forms

from .models import Calendar, Ticket, BookingSettings

class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['name', 'url', 'username', 'password', 'main_calendar']
        labels = {
            'name': 'Name',
            'url': 'CalDAV-URL',
            'username': 'Benutzername',
            'password': 'Passwort',
            'main_calendar': 'Hauptkalender',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.TextInput(attrs={'class': 'form-control'}),
            'main_calendar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketForm(forms.ModelForm):
    ticket_customer_link = forms.CharField(label='Link für Kunden', widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = Ticket
        fields = ['name', 'first_available_date', 'duration', 'expiry', 'generate_jitsi_link']
        labels = {
            'name': 'Name',
            'first_available_date': 'Erstes verfügbares Datum',
            'duration': 'Dauer (Stunden)',
            'expiry': 'Ablaufdatum',
            'generate_jitsi_link': 'Generate Jitsi Link',
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
            'earliest_booking_time': 'Früheste Buchungszeit',
            'latest_booking_end': 'Spätetestes Terminende (Wann hast Du Feierabend?)',
            'monday': 'Termine am Montag möglich',
            'tuesday': 'Termine am Dienstag möglich',
            'wednesday': 'Termine am Mittwoch möglich',
            'thursday': 'Termine am Donnerstag möglich',
            'friday': 'Termine am Freitag möglich',
            'saturday': 'Termine am Samstag möglich',
            'sunday': 'Termine am Sonntag möglich',
            'jitsi_server': 'Jitsi Server Basis-URL',
            'maximum_future_booking_time': 'Maximale Buchungszeit in der Zukunft (in Tagen):',
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
            # Disably "Tage" in the end of the input field
            'maximum_future_booking_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
