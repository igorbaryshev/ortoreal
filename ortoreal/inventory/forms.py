from django import forms
from django.utils import timezone
from django.core.validators import MinValueValidator

from inventory.models import InventoryLog, Item


class DatePicker(forms.DateInput):
    input_type = "date"


class InventoryLogForm(forms.ModelForm):
    class Meta:
        model = InventoryLog
        fields = (
            "id",
            "operation",
            "patient",
            "prosthetist",
            "date",
            "comment",
        )
        widgets = {
            "date": DatePicker(
                attrs={"value": timezone.now}, format="%Y-%m-%d"
            )
        }


class ItemAddForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label="Количество",
        required=True,
        min_value=1,
        initial=0,
    )

    class Meta:
        model = Item
        fields = ("part", "warehouse", "quantity")


ItemFormSet = forms.formset_factory(
    ItemAddForm,
    # can_delete=True,
    extra=1,
)
