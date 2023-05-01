from typing import Any, Mapping, Optional, Type, Union
from django import forms
from django.db.models import Count, Q
from django.forms.utils import ErrorList
from django.utils import timezone
from django.contrib.auth import get_user_model

from inventory.models import InventoryLog, Item, Part
from clients.models import Client, Job

User = get_user_model


class ProsthetistJobsForm(forms.Form):
    job = forms.ModelChoiceField(
        queryset=Job.objects.none(),
        label="Клиент",
        widget=forms.Select(
            attrs={
                "onchange": "clearFormSet(); this.form.submit();",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["job"].queryset = Job.objects.filter(
            prosthetist=user
        ).order_by("-client")
