from django import forms
from django.utils import timezone

from clients.models import Client, Contact, Comment


class DatePicker(forms.DateInput):
    input_type = "date"


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = "__all__"

        widgets = {
            "call_date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            )
        }


ContactFormSet = forms.formset_factory(
    form=ContactForm,
    extra=1,
)
