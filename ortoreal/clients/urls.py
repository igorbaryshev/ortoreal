from django.urls import include, path

from clients import views

app_name = "clients"

urlpatterns = [
    path("contacts/", views.contacts, name="contacts"),
    path("contacts/add/", views.add_contact, name="add_contact"),
    path("contacts/edit/<int:pk>", views.edit_contact, name="edit_contact"),
    path("clients/", views.ClientListView.as_view(), name="clients"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client"),
]
