from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("calendars/", views.calendars, name="calendars"),
    path("create_calendar/", views.create_calendar, name="create_calendar"),
    path("edit_calendar/<int:calendar_id>/", views.edit_calendar, name="edit_calendar"),
    path("delete_calendar/<int:calendar_id>/", views.delete_calendar, name="delete_calendar"),

    path("tickets/", views.tickets, name="tickets"),
    path("delete_ticket/<str:guid>/", views.delete_ticket, name="delete_ticket"),
    path("edit_ticket/<str:guid>/", views.edit_ticket, name="edit_ticket"),

    path("ticket/<str:guid>/", views.ticket_customer_view, name="ticket_customer_view"),
]