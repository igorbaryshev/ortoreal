from django import forms
from django.db.models import Count
from django.utils import timezone

from inventory.models import InventoryLog, Item, Part


class DatePicker(forms.DateInput):
    input_type = "date"


class InventoryLogFormMeta:
    model = InventoryLog
    widgets = {
        "date": DatePicker(
            attrs={"value": timezone.now}, format="%Y-%m-%d"
        )
    }


class InventoryAddForm(forms.ModelForm):
    operation = forms.ChoiceField(
        label="Операция",
        choices=InventoryLog.PartialLogAction.choices,
    )

    class Meta(InventoryLogFormMeta):
        fields = (
            "operation",
            "date",
            "comment",
        )


class InventoryTakeForm(forms.ModelForm):
    class Meta(InventoryLogFormMeta):
        fields = (
            "prosthetist",
            "client",
            "date",
            "comment",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prosthetist"].empty_label = "---выбрать---"
        self.fields["client"].empty_label = "---выбрать---"


class ItemForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label="Кол-во",
        required=True,
        min_value=1,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["part"].empty_label = "---выбрать---"


class ItemAddForm(ItemForm):
    class Meta:
        model = Item
        fields = ("part", "warehouse", "quantity")


ItemAddFormSet = forms.formset_factory(
    ItemAddForm,
    extra=1,
)


class ItemTakeForm(ItemForm):
    queryset = Part.objects.order_by("id").annotate(total=Count("items"))

    total = forms.ModelChoiceField(
        label="Наличие",
        queryset=queryset.values_list("total", flat=True),
        required=False,
        widget=forms.Select(attrs={"disabled": "disabled"}),
    )

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        part = self.cleaned_data.get("part")
        if quantity and part:
            total = self.queryset.get(id=part.id).total
            if quantity > total:
                raise forms.ValidationError(f"Не больше {total}")
        return quantity

    class Meta:
        model = Item
        fields = ("part", "quantity", "total")


ItemTakeFormSet = forms.formset_factory(
    ItemTakeForm,
    extra=1,
)
