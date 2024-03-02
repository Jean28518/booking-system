from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=200, label="Benutzername")
    password = forms.CharField(max_length=200, label="Passwort", widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=200, label="Benutzername")
    password = forms.CharField(max_length=200, label="Passwort", widget=forms.PasswordInput)
    password_repeat = forms.CharField(max_length=200, label="Passwort wiederholen", widget=forms.PasswordInput)

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(max_length=200, label="Altes Passwort", widget=forms.PasswordInput)
    new_password = forms.CharField(max_length=200, label="Neues Passwort", widget=forms.PasswordInput)
    new_password_repeat = forms.CharField(max_length=200, label="Neues Passwort wiederholen", widget=forms.PasswordInput)

class ProfileForm(forms.Form):
    username = forms.CharField(max_length=200, label="Benutzername", disabled=True, required=False)
    first_name = forms.CharField(max_length=200, label="Vorname", required=False)
    last_name = forms.CharField(max_length=200, label="Nachname", required=False)
    email = forms.EmailField(max_length=200, label="E-Mail", required=False)
    phone = forms.CharField(max_length=200, label="Telefonnummer", required=False)
    picture = forms.ImageField(label="Profilbild", required=False)