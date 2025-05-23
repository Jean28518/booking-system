from django.shortcuts import render, redirect
import accounts.forms as forms
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _

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
                message = _("Username or password incorrect")

    login_form = forms.LoginForm()
    register_url = reverse("register")
    return render(request, "root/generic_form.html", 
                  {"form": login_form,
                    "title": _("Login"),
                    "submit": _("Login"),
                    "message": message,
                    "content_after": _("No account yet?") + f" <a href='{register_url}'>" + _("Register") + "</a>"
                   })

def register_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect("index")
    if cfg.get_value("enable_registration", False) == False and User.objects.count() > 0:
        return templates.message(request, _("Registration disabled. Please contact the administrator."), "index")
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
                    message = _("Username already taken")
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
                message = _("Passwords do not match")
    register_form = forms.RegisterForm()
    login_url = reverse("login")
    return render(request, "root/generic_form.html", 
                  {"form": register_form,
                    "title": _("Register"),
                    "submit": _("Register"),
                    "message": message,
                    "content_after": _("Already have an account?") + f"<a href='{login_url}'>" + _("Login") + "</a>"
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
                    message = _("Password changed successfully")
                else:
                    message = _("Old password incorrect")
            else:
                message = _("New passwords do not match")
    change_password_form = forms.ChangePasswordForm()
    return render(request, "root/generic_form.html", 
                  {"form": change_password_form,
                    "title": _("Change password"),
                    "submit": _("Change"),
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
            message = _("Profile updated")
    profile_form = forms.ProfileForm(initial={"username": user.username, "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "phone": user.profile.phone, "picture": user.profile.picture})
    return render(request, "root/generic_form.html", 
                  {"form": profile_form,
                    "title": _("Profile"),
                    "submit": _("Save"),
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
            cfg.set_value("skip_ssl_check", form.cleaned_data["skip_ssl_check"])
            message = _("Settings saved.")
        else:
            message = _("Invalid input")
    form.fields["enable_registration"].initial = cfg.get_value("enable_registration", False)
    form.fields["skip_ssl_check"].initial = cfg.get_value("skip_ssl_check", False)

    return render(request, 'root/generic_form.html', {"title": _("Administrator settings"), "form": form, "back": reverse("index"), "submit": _("Save"), "message": message})