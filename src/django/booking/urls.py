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
    path("customer_cancel_ticket/<str:guid>/", views.customer_cancel_ticket, name="customer_cancel_ticket"),
    path("customer_change_date/<str:guid>/", views.customer_change_date, name="customer_change_date"),


    path("settings/", views.booking_settings, name="booking_settings"),
    path("set_timezone/", views.set_timezone, name="set_timezone"),

    path("select_slot/<str:guid>/<str:date>/<str:start_time>/", views.select_slot, name="select_slot"),

    path("recurring_ticket/<str:guid>/", views.recurring_ticket, name="recurring_ticket"),
    path("create_ticket_from_recurring/<str:guid>/", views.create_ticket_from_recurring, name="create_ticket_from_recurring"),
]