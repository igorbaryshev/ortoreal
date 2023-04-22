from clients.models import Client, Comment, Contact
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.core import serializers
from django.db.models.functions import Concat
from django.db import models
from clients.forms import ContactForm, ClientContactForm
from django.shortcuts import get_object_or_404


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
