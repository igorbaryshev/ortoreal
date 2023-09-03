from django.urls import include, path

from clients import views

app_name = "clients"

urlpatterns = [
    path("", views.ClientsListView.as_view(), name="index"),
    path("contacts/", views.contacts, name="contacts"),
    path("contacts/add/", views.add_contact, name="add_contact"),
    path("contacts/edit/<int:pk>", views.edit_contact, name="edit_contact"),
    path("clients/", views.ClientsListView.as_view(), name="clients"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="job"),
    # path("jobs/all/", views.AllClientsListView.as_view(), name="all_jobs"),
    path("clients/<int:pk>/", views.ClientView.as_view(), name="client"),
]
