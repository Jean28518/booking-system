from django.shortcuts import render
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

import mails.forms as forms
import cfg.cfg as cfg

@staff_member_required
def email_settings(request):
    form = forms.EmailSettings()
    if request.method == "POST":
        form = forms.EmailSettings(request.POST)
        if form.is_valid():
            for field in form.fields:
                if field == "password" and form.cleaned_data[field] == "":
                    continue
                cfg.set_value(f"email_{field}", form.cleaned_data[field])
    
    for field in form.fields:
        form.fields[field].initial = cfg.get_value(f"email_{field}", "")

    test_mail_url = reverse("send_test_email")
    return render(request, 'root/generic_form.html', {'form': form, 'title': 'E-Mail Einstellungen', 'submit': 'Speichern', 'content_after': '<a href="' + test_mail_url + '">Test E-Mail versenden</a>'})

@staff_member_required
def send_test_email(request):
    user = request.user
    if user.email == "":
        return render(request, "root/message.html", {"message": "Bitte E-Mail Adresse in den Benutzereinstellungen hinterlegen", "url": reverse("profile")})
    if cfg.get_value("email_user", "") == "":
        return render(request, "root/message.html", {"message": "Bitte E-Mail Einstellungen konfigurieren", "url": reverse("email_settings")})
    
    try:
        send_mail(
            'Test E-Mail',
            'Dies ist eine Test E-Mail',
            cfg.get_value("email_user", ""),
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        return render(request, "root/message.html", {"message": f"Fehler beim Versenden der E-Mail: {e}", "url": reverse("email_settings")})
    
    return render(request, "root/message.html", {"message": "Test E-Mail wurde versendet"})