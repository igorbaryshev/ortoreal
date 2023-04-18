from clients.forms import ContactFormSet
from clients.models import Client, Comment, Contact
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.core import serializers
from django.db.models.functions import Concat
from django.db import models


@login_required
def contacts(request):
    table_head = ["ID", "ФИО"] + Contact.get_field_names()[4:]
    contact_list = Contact.objects.order_by('id')
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
    formset = ContactFormSet(request.POST or None, prefix="contact")

    if request.method == "POST" and formset.is_valid():
        for form in formset:
            form.save()

        return redirect("clients:contact")

    context = {
        "formset": formset,
    }

    return render(request, "clients/create_contact.html", context)
