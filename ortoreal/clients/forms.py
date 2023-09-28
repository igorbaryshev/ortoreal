from collections.abc import Mapping
from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from django.utils import timezone

from clients.models import Client, Comment, Contact, Job

User = get_user_model()


class DatePicker(forms.DateInput):
    input_type = "date"


class ClientContactForm(forms.ModelForm):
    # how_contacted = forms.ChoiceField(
    #     choices=get_contact_type_choices,
    #     label=Client._meta.get_field("how_contacted").verbose_name,
    # )

    class Meta:
        model = Client
        fields = (
            "last_name",
            "first_name",
            "surname",
            # "how_contacted",
            "prosthetist",
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"
        exclude = ["client"]

        widgets = {
            "call_date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            ),
            "MTZ_date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            ),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"


class JobForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].widget = DatePicker(
            attrs={
                "value": timezone.now,
            },
            format="%Y-%m-%d",
        )

    class Meta:
        model = Job
        fields = [
            "client",
            "how_contacted",
            "prosthetist",
            "prosthesis",
            "date",
        ]


class JobClientForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "how_contacted",
            "prosthetist",
            "prosthesis",
            "date",
        ]


class ClientContactForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["last_name", "first_name", "surname", "phone", "birth_date"]
