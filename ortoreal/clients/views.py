from decimal import Decimal
from typing import Any, Dict, Optional

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, Count, F, Max, Q, When
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView

import django_tables2 as tables

from clients.forms import (
    ClientContactForm,
    ClientForm,
    ContactForm,
    JobClientForm,
    JobForm,
)
from clients.models import Client, Comment, Contact, Job
from clients.tables import ClientProsthesisListTable, ClientsTable
from inventory.tables import ClientItemsTable

# from clients.tables import ClientPartsTable, ClientsTable


CLIENTS_PER_PAGE = 20


@login_required
def contacts(request):
    table_head = ["ID", "ФИО"] + Contact.get_field_names()[4:]
    contact_list = Contact.objects.order_by("id")
    paginator = Paginator(contact_list, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "table_head": table_head,
        "page_obj": page_obj,
    }

    return render(request, "clients/contacts.html", context)


@login_required
def add_contact(request):
    form_client = ClientContactForm(request.POST or None, prefix="contact")
    form_contact = ContactForm(request.POST or None, prefix="contact")

    if (
        request.method == "POST"
        and form_client.is_valid()
        and form_contact.is_valid()
    ):
        client = form_client.save()
        contact = form_contact.save(commit=False)
        contact.save(client=client)

        return redirect("clients:contacts")

    context = {
        "form_client": form_client,
        "form_contact": form_contact,
    }

    return render(request, "clients/create_contact.html", context)


@login_required
def edit_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form_client = ClientContactForm(request.POST, instance=contact.client)
    form_contact = ContactForm(request.POST, instance=contact)

    if (
        request.method == "POST"
        and form_client.is_valid()
        and form_contact.is_valid()
    ):
        form_client.save()
        form_contact.save()

        return redirect("clients:contacts")

    context = {
        "form_client": form_client,
        "form_contact": form_contact,
    }

    return render(request, "clients/create_contact.html", context)


# class ClientListView(
#     LoginRequiredMixin, UserPassesTestMixin, tables.SingleTableView
# ):
#     """
#     View клиентов протезиста.
#     """

#     table_class = ClientsTable

#     def test_func(self) -> bool:
#         return self.request.user.is_prosthetist

#     def get_queryset(self) -> QuerySet[Any]:
#         queryset = Job.objects.filter(prosthetist=self.request.user).order_by(
#             "-date"
#         )
#         return queryset

#     def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
#         context = super().get_context_data(**kwargs)
#         context["title"] = f"{self.request.user}. Клиенты."

#         return context


class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View подробностей о клиенте.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        table = ClientItemsTable(
            job.items.annotate(
                item_count=Count("part"),
                vendor_code=F("part__vendor_code"),
                name=F("part__name"),
            ).order_by("vendor_code")
        )
        context = {"table": table, "job": job}

        return render(request, "clients/client.html", context)


# class AllClientsListView(ClientListView):
#     """
#     View всех клиентов для менеджера.
#     """

#     def test_func(self) -> bool:
#         return self.request.user.is_manager

#     def get_queryset(self) -> QuerySet[Any]:
#         queryset = Job.objects.order_by("-date")
#         return queryset

#     def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
#         context = super(tables.SingleTableView, self).get_context_data(
#             **kwargs
#         )
#         context["title"] = "Все клиенты."

#         return context


class ClientsListView(
    LoginRequiredMixin, UserPassesTestMixin, tables.SingleTableView
):
    """
    View всех клиентов со статусами работ.
    """

    table_class = ClientsTable
    paginate_by = CLIENTS_PER_PAGE

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist or self.request.user.is_manager

    def get_queryset(self):
        qs = Client.objects.annotate(
            jobs_count=Count("jobs"),
            jobs_in_progress=Count("jobs", filter=Q(jobs__is_finished=False)),
            latest_job_date=Max("jobs__date"),
        ).order_by("-latest_job_date")
        print(qs.values("latest_job_date"))
        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = f"{self.request.user}. Клиенты."

        return context


class ClientView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View страницы клиента.
    """

    def test_func(self) -> bool:
        return self.request.user.is_manager or self.request.user.is_prosthetist

    def get_client(self):
        pk = self.kwargs.get("pk")
        client = get_object_or_404(Client, pk=pk)
        return client

    def get(self, request, pk):
        table = ClientProsthesisListTable(self.get_queryset())
        client = self.get_client()
        form = ClientForm(instance=client)
        context = {"table": table, "client": client, "form": form}

        return render(request, "clients/client.html", context)

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(data=request.POST or None, instance=client)
        if form.is_valid():
            form.save()
        table = ClientProsthesisListTable(self.get_queryset())
        client = self.get_client()
        context = {"table": table, "client": client, "form": form}
        return render(request, "clients/client.html", context)

    def get_queryset(self):
        queryset = Job.objects.filter(client=self.get_client()).order_by(
            "-date"
        )
        return queryset


class JobCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View создания работы.
    """

    def test_func(self) -> bool:
        return self.request.user.is_manager or self.request.user.is_prosthetist

    def get(self, request, pk=None):
        if pk is not None:
            client = get_object_or_404(Client, pk=pk)
            form = JobClientForm(initial={"client": client})
            context = {"client": client, "form": form}
        else:
            context = {"form": JobForm()}
        return render(request, "clients/job_add.html", context)

    def post(self, request, pk=None):
        if pk is not None:
            client = get_object_or_404(Client, pk=pk)
            form = JobClientForm(request.POST or {"client": client})
            if form.is_valid():
                job = form.save(commit=False)
                job.client = client
                job.save()
                return redirect("clients:client", pk=client.pk)
            context = {"form": form, "client": client}
        else:
            form = JobForm(request.POST or None)
            if form.is_valid():
                job = form.save()
                client = job.client
                return redirect("clients:client", pk=client.pk)
            context = {"form": form}

        return render(request, "clients/job_add.html", context)


class ContactCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View создания обращения.
    """

    def test_func(self) -> bool:
        return self.request.user.is_manager or self.request.user.is_prosthetist

    def get(self, request, pk=None):
        client = get_object_or_404(Client, pk=pk)
        form = ContactForm(initial={"client": client})
        context = {"form": form, "client": client}
        return render(request, "clients/contact_add.html", context)

    def post(self, request, pk=None):
        if pk is not None:
            client = get_object_or_404(Client, pk=pk)
        form = ContactForm(request.POST or {"client": client} or None)

        if form.is_valid():
            contact = form.save(commit=False)
            contact.client = client
            contact.save()
            return redirect("clients:client", pk=client.pk)

        context = {"form": form, "client": client}
        return render(request, "clients/contact_add.html", context)


class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View создания клиента.
    """

    def test_func(self) -> bool:
        return self.request.user.is_manager or self.request.user.is_prosthetist

    def get(self, request):
        form_client = ClientContactForm()
        form_contact = ContactForm()
        context = {"form_client": form_client, "form_contact": form_contact}
        return render(request, "clients/add.html", context)

    @transaction.atomic
    def post(self, request):
        form_client = ClientContactForm(request.POST or None)
        form_contact = ContactForm(request.POST or None)

        if form_client.is_valid():
            client = form_client.save()
            if form_contact.is_valid():
                contact = form_contact.save(commit=False)
                contact.client = client
                contact.save()
                return redirect("clients:client", pk=client.pk)

        context = {"form_client": form_client, "form_contact": form_contact}
        return render(request, "clients/add.html", context)
