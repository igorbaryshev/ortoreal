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
    path("job/add/", views.JobCreateView.as_view(), name="add_job"),
    # path("jobs/all/", views.AllClientsListView.as_view(), name="all_jobs"),
    path("clients/<int:pk>/", views.ClientView.as_view(), name="client"),
    path(
        "clients/<int:pk>/add_job/",
        views.JobCreateView.as_view(),
        name="add_job_client",
    ),
    path(
        "clients/<int:pk>/add_contact/",
        views.ContactCreateView.as_view(),
        name="add_contact",
    ),
    path(
        "clients/add/",
        views.ClientCreateView.as_view(),
        name="add_client",
    ),
]
