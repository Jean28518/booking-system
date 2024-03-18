from django import forms

class EmailSettings(forms.Form):
    server = forms.CharField(label="E-Mail Server", max_length=100, widget=forms.TextInput(attrs={"placeholder": "mail.example.com"}), required=True)
    port = forms.IntegerField(label="E-Mail Port", min_value=0, max_value=10000, widget=forms.NumberInput(attrs={"placeholder": "587"}), required=True)
    user = forms.CharField(label="E-Mail Benutzername", max_length=100, widget=forms.TextInput(attrs={"placeholder": "example@example.com"}), required=True)
    password = forms.CharField(label="E-Mail Passwort", max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Passwort"}),  required=False)
    encryption = forms.ChoiceField(label="E-Mail Verschlüsselung", choices=[("TLS", "TLS"), ("SSL", "SSL")], widget=forms.Select(attrs={"class": "form-control"}), required=True)