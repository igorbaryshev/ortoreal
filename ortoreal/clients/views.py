from typing import Any, Dict

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

import django_tables2 as tables

from clients.forms import ClientContactForm, ContactForm
from clients.models import Client, Comment, Contact, Job

# from clients.tables import ClientPartsTable, ClientsTable


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
#     View-класс клиентов протезиста.
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
    View-класс подробностей о клиенте.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        table = ClientPartsTable(
            job.items.annotate(
                item_count=Count("part"),
                vendor_code=F("part__vendor_code"),
                part_name=F("part__name"),
            ).order_by("vendor_code")
        )
        context = {"table": table, "job": job}

        return render(request, "clients/client.html", context)


# class AllClientsListView(ClientListView):
#     """
#     View-класс всех клиентов для менеджера.
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
