from django import forms
from django.utils.translation import gettext as _

class EmailSettings(forms.Form):
    server = forms.CharField(label=_("E-Mail Server"), max_length=100, widget=forms.TextInput(attrs={"placeholder": _("mail.example.com")}), required=True)
    port = forms.IntegerField(label=_("E-Mail Port"), min_value=0, max_value=10000, widget=forms.NumberInput(attrs={"placeholder": _("587")}), required=True)
    user = forms.CharField(label=_("E-Mail Username"), max_length=100, widget=forms.TextInput(attrs={"placeholder": _("example@example.com")}), required=True)
    password = forms.CharField(label=_("E-Mail Password"), max_length=100, widget=forms.PasswordInput(attrs={"placeholder": _("Password")}), required=False)
    encryption = forms.ChoiceField(label=_("E-Mail Encryption"), choices=[("TLS", "TLS"), ("SSL", "SSL")], widget=forms.Select(attrs={"class": "form-control"}), required=True)