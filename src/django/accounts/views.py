from django.shortcuts import render, redirect
import accounts.forms as forms
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from accounts.models import Profile
import os

import cfg.cfg as cfg
import root.templates as templates


# Create your views here.
def login_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect("index")
    message = ""
    if request.method == "POST":
        login_form = forms.LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data["username"]
            password = login_form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")
            else:
                message = "Benutzername oder Passwort falsch"

    login_form = forms.LoginForm()
    register_url = reverse("register")
    return render(request, "root/generic_form.html", 
                  {"form": login_form,
                    "title": "Login",
                    "submit": "Einloggen",
                    "message": message,
                    "content_after": f"Noch keinen Account? <a href='{register_url}'>Registrieren</a>"
                   })

def register_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect("index")
    if cfg.get_value("enable_registration", False) == False and User.objects.count() > 0:
        return templates.message(request, "Registrierung deaktiviert. Bitte kontaktieren Sie den Administrator.", "index")
    message = ""
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data["username"]
            password = register_form.cleaned_data["password"]
            password_repeat = register_form.cleaned_data["password_repeat"]
            if password == password_repeat:
                # Check if already user with this username exists
                if User.objects.filter(username=username).exists():
                    message = "Benutzername bereits vergeben"
                else:
                    user = User.objects.create_user(username, password=password)
                    profile = Profile(user=user)
                    profile.save()
                    user.profile = profile
                    if User.objects.count() == 1:
                        user.is_staff = True
                        user.is_superuser = True
                    user.save()
                return redirect("login")
            else:
                message = "Passwörter stimmen nicht überein"
    register_form = forms.RegisterForm()
    login_url = reverse("login")
    return render(request, "root/generic_form.html", 
                  {"form": register_form,
                    "title": "Registrieren",
                    "submit": "Registrieren",
                    "message": message,
                    "content_after": f"Schon einen Account? <a href='{login_url}'>Einloggen</a>"
                   })

def logout_view(request):
    logout(request)
    return redirect("index")

@login_required()
def change_password_view(request):
    message = ""
    if request.method == "POST":
        change_password_form = forms.ChangePasswordForm(request.POST)
        if change_password_form.is_valid():
            old_password = change_password_form.cleaned_data["old_password"]
            new_password = change_password_form.cleaned_data["new_password"]
            new_password_repeat = change_password_form.cleaned_data["new_password_repeat"]
            if new_password == new_password_repeat:
                user = request.user
                if user.check_password(old_password):
                    user.set_password(new_password)
                    user.save()
                    login(request, user)
                    message = "Passwort erfolgreich geändert."
                else:
                    message = "Altes Passwort falsch"
            else:
                message = "Neue Passwörter stimmen nicht überein"
    change_password_form = forms.ChangePasswordForm()
    return render(request, "root/generic_form.html", 
                  {"form": change_password_form,
                    "title": "Passwort ändern",
                    "submit": "Ändern",
                    "back": reverse("index"),
                    "message": message
                   })


@login_required()
def profile_view(request):
    message = ""
    user = request.user
    if request.method == "POST":
        profile_form = forms.ProfileForm(request.POST, request.FILES)
        if profile_form.is_valid():
            user.first_name = profile_form.cleaned_data["first_name"]
            user.last_name = profile_form.cleaned_data["last_name"]
            user.email = profile_form.cleaned_data["email"]
            user.profile.phone = profile_form.cleaned_data["phone"]
            if request.FILES.get("picture"):
                path = handle_uploaded_file(request.FILES["picture"], user.username)
                user.profile.picture = path
            if request.POST.get("picture-clear"):
                user.profile.picture = ""
            user.profile.save()
            user.save()
            message = "Profil erfolgreich geändert."
    profile_form = forms.ProfileForm(initial={"username": user.username, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "phone": user.profile.phone, "picture": user.profile.picture})
    return render(request, "root/generic_form.html", 
                  {"form": profile_form,
                    "title": "Profil",
                    "submit": "Ändern",
                    "back": reverse("index"),
                    "message": message
                   })


def handle_uploaded_file(f, username, allowed_extensions=["png", "jpg", "jpeg", "webp"]):
    # Get file extension
    file_extension = f.name.split(".")[-1]
    if file_extension not in allowed_extensions:
        return None
    # Ensure that the folders exist
    os.makedirs("media/profile_pictures", exist_ok=True)
    with open(f"media/profile_pictures/{username}.{file_extension}", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return f"profile_pictures/{username}.{file_extension}"


@staff_member_required()
def admin_settings(request):
    message = ""
    form = forms.AdminSettingsForm()
    if request.method == "POST":
        form = forms.AdminSettingsForm(request.POST)
        if form.is_valid():
            cfg.set_value("enable_registration", form.cleaned_data["enable_registration"])
            message = "Änderungen abgespeichert."
        else:
            message = "Fehler beim Bearbeiten der Einstellungen."
    form.fields["enable_registration"].initial = cfg.get_value("enable_registration", False)
    return render(request, 'root/generic_form.html', {"title": "Administrator-Einstellungen", "form": form, "back": reverse("index"), "submit": "Speichern", "message": message})