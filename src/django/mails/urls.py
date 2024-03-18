from django.urls import path
from . import views

urlpatterns = [
    path('email_settings/', views.email_settings, name='email_settings'),
    path('send_test_email/', views.send_test_email, name='send_test_email'),
]