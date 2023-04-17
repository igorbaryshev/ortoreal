from django.urls import include, path

from clients import views

app_name = "clients"

urlpatterns = [
    path("contacts/", views.contacts, name="contacts"),
    path("contacts/add/", views.add_contact, name="add_contacts"),
]
