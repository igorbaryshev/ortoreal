from django import forms
from django.db.models import Count, Q
from django.utils import timezone

from inventory.models import InventoryLog, Item, Part
from clients.models import Client, Job


class DatePicker(forms.DateInput):
    """
    Выбор даты.
    """

    input_type = "date"


class InventoryLogFormMeta:
    """
    Мета формы записи в логе
    """

    model = InventoryLog
    widgets = {
        "date": DatePicker(attrs={"value": timezone.now}, format="%Y-%m-%d"),
        "comment": forms.TextInput(attrs={"size": 80}),
    }


class InventoryAddForm(forms.ModelForm):
    """
    Форма лога прихода.
    """

    class Meta(InventoryLogFormMeta):
        fields = (
            "date",
            "comment",
        )


class InventoryTakeForm(forms.ModelForm):
    """
    Форма лога расхода/возврата.
    """

    operation = forms.ChoiceField(
        label="Операция",
        choices=InventoryLog.PartialLogAction.choices,
        widget=forms.Select(attrs={"onchange": "this.form.submit()"}),
    )
    client = forms.ModelChoiceField(
        label="Клиент",
        queryset=Job.objects.none(),
        widget=forms.Select(attrs={"onchange": "this.form.submit()"}),
    )

    class Meta(InventoryLogFormMeta):
        fields = (
            "operation",
            "client",
            "comment",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].empty_label = "---выбрать---"


class ItemForm(forms.ModelForm):
    """
    Базовая форма комплектующего на складе.
    """

    quantity = forms.IntegerField(
        label="Кол-во",
        required=True,
        min_value=1,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        part_field = self.fields["part"]
        part_field.empty_label = "---выбрать---"
        part_field.queryset = part_field.queryset.order_by("vendor_code")


class ItemAddForm(ItemForm):
    """
    Форма добавления/возврата комплектующего на склад.
    """

    class Meta:
        model = Item
        fields = ("part", "warehouse", "quantity")


ItemAddFormSet = forms.formset_factory(
    ItemAddForm,
    extra=1,
)


class ItemTakeForm(ItemForm):
    """
    Форма расхода комплектующего.
    """

    queryset = Part.objects.order_by("vendor_code").annotate(
        total=Count("items", filter=Q(items__warehouse__in=["s1", "s2"]))
    )

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
        if not quantity:
            quantity = 0
        print(quantity)
        return quantity

    class Meta:
        model = Item
        fields = ("part", "quantity", "total")


ItemTakeFormSet = forms.formset_factory(
    ItemTakeForm,
    extra=1,
)


class PartAddForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ("vendor_code", "name", "units", "price", "vendor", "note")


PartAddFormSet = forms.modelformset_factory(
    model=Part,
    extra=1,
    exclude=("id",),
)


class ItemReturnForm(forms.Form):
    return_item = forms.BooleanField(label="Вернуть", required=False)
    part = forms.CharField(label="Артикул", required=False)
    quantity = forms.IntegerField(
        label="Количество", min_value=0, required=False
    )
    part_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Item
        fields = ("return_item", "part", "quantity", "part_id")


ItemReturnFormSet = forms.formset_factory(form=ItemReturnForm, extra=0)
