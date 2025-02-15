from django import forms
from django.utils.translation import gettext as _


class LoginForm(forms.Form):
    username = forms.CharField(max_length=200, label=_("Username"))
    password = forms.CharField(max_length=200, label=_("Password"), widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=200, label=_("Username"))
    password = forms.CharField(max_length=200, label=_("Password"), widget=forms.PasswordInput)
    password_repeat = forms.CharField(max_length=200, label=_("Repeat password"), widget=forms.PasswordInput)

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(max_length=200, label=_("Old password"), widget=forms.PasswordInput)
    new_password = forms.CharField(max_length=200, label=_("New password"), widget=forms.PasswordInput)
    new_password_repeat = forms.CharField(max_length=200, label=_("Repeat new password"), widget=forms.PasswordInput)

class ProfileForm(forms.Form):
    username = forms.CharField(max_length=200, label=_("Username"), disabled=True, required=False)
    first_name = forms.CharField(max_length=200, label=_("First name"), required=False)
    last_name = forms.CharField(max_length=200, label=_("Last name"), required=False)
    email = forms.EmailField(max_length=200, label=_("E-Mail"), required=False)
    phone = forms.CharField(max_length=200, label=_("Phone"), required=False)
    picture = forms.ImageField(label=_("Profile picture"), required=False)


class AdminSettingsForm(forms.Form):
    enable_registration = forms.BooleanField(label=_("Enable registration"), required=False)
    skip_ssl_check = forms.BooleanField(label=_("Skip SSL check"), required=False)