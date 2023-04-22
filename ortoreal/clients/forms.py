from django import forms
from django.utils import timezone

from clients.models import Client, Contact, Comment, get_contact_type_choices


class DatePicker(forms.DateInput):
    input_type = "date"


class ClientContactForm(forms.ModelForm):
    how_contacted = forms.ChoiceField(
        choices=get_contact_type_choices,
        label=Client._meta.get_field("how_contacted").verbose_name,
    )

    class Meta:
        model = Client
        fields = (
            "last_name",
            "first_name",
            "surname",
            "how_contacted",
            "prosthetist",
        )


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"
        exclude = ("client",)

        widgets = {
            "call_date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            ),
            "MTZ_date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            ),
        }
