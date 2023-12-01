from decimal import Decimal

from django import forms
from django.utils import timezone

from clients.models import Client, Job
from inventory.models import InventoryLog, Invoice, Item, Order, Part, Prosthesis


class DatePicker(forms.DateInput):
    input_type = "date"


class DateTimePicker(forms.DateInput):
    """
    Выбор даты.
    """

    input_type = "datetime-local"


class InventoryLogFormMeta:
    """
    Мета формы записи в логе
    """

    model = InventoryLog
    widgets = {
        "date": DateTimePicker(attrs={"value": timezone.now}, format="%Y-%m-%d %H:%M"),
        "comment": forms.Textarea(attrs={"cols": 80, "rows": 2}),
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

    job = forms.ModelChoiceField(
        queryset=Job.objects.order_by("-client"),
        label="Клиент",
        widget=forms.Select(
            attrs={
                "onchange": "clearFormSet(); this.form.submit();",
            }
        ),
    )

    class Meta(InventoryLogFormMeta):
        fields = (
            "job",
            "comment",
        )

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if user.is_prosthetist:
            self.fields["job"].queryset = (
                self.fields["job"].queryset.filter(prosthetist=user).order_by("-client")
            )

        self.fields["job"].empty_label = "---выбрать---"


class ItemForm(forms.ModelForm):
    """
    Базовая форма комплектующего на складе.
    """

    quantity = forms.IntegerField(
        label="Количество",
        required=True,
        min_value=0,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        part_field = self.fields["part"]
        part_field.empty_label = "---выбрать---"
        part_field.queryset = part_field.queryset.order_by("vendor_code")
        if "price" in self.fields:
            self.fields["price"].widget.attrs["class"] = "text-end"
        self.fields["quantity"].widget.attrs["class"] = "text-center"


class ReceptionItemForm(ItemForm):
    """
    Форма прихода модели комплектующей на склад.
    """

    # warehouse = forms.ChoiceField(
    # label="Склад", choices=Item.Warehouse.choices, required=True
    # )
    # part = forms.ModelChoiceField()
    vendor2 = forms.BooleanField(label="Поставщик 2", required=False)
    quantity = forms.IntegerField(
        label="Количество", required=True, min_value=0, initial=0
    )
    price = forms.DecimalField(
        label="Цена, руб.",
        required=True,
        initial=Decimal("0.00"),
    )

    class Meta:
        model = Item
        fields = ("part", "quantity", "price", "vendor2")


# Формсет прихода комплектующих
ReceptionItemFormSet = forms.formset_factory(
    ReceptionItemForm,
    extra=1,
)


class ItemTakeForm(ItemForm):
    """
    Форма расхода комплектующего.
    """

    available = forms.ChoiceField(
        label="Наличие",
        choices=(),
        required=False,
        initial="-",
        widget=forms.Select(attrs={"hidden": ""}),
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = queryset
        if queryset:
            self.fields["part"].queryset = queryset
            self.fields["available"].choices = [(0, "-")] + list(
                queryset.values_list("id", "available")
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        part = self.cleaned_data.get("part")
        if quantity and part:
            available = part.available
            if quantity > available:
                raise forms.ValidationError(f"Не больше {available}")
        else:
            quantity = 0
        return quantity

    class Meta:
        model = Item
        fields = ("part", "quantity", "available")


ItemTakeFormSet = forms.formset_factory(
    ItemTakeForm,
    extra=1,
)


class ItemReturnForm(forms.Form):
    part = forms.CharField(label="Артикул", required=False)
    quantity = forms.IntegerField(label="Количество", min_value=0, required=False)
    part_id = forms.IntegerField(widget=forms.HiddenInput())


ItemReturnFormSet = forms.formset_factory(
    form=ItemReturnForm,
    extra=0,
)


class JobSelectForm(forms.Form):
    """
    Форма выбора работы для страницы выбора комплектации.
    """

    job = forms.ModelChoiceField(
        queryset=Job.objects.order_by("-client"),
        label="Клиент",
        widget=forms.Select(
            attrs={
                "onchange": "clearFormSet(); this.form.submit();",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not user.is_manager:
            self.fields["job"].queryset = self.fields["job"].queryset.filter(
                prosthetist=user
            )  # .order_by("-client")

        self.fields["job"].empty_label = "---выбрать---"


class ClientSelectForm(forms.Form):
    """
    Форма выбора клиента для страницы выбора комплектации.
    """

    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(jobs__isnull=False).order_by(
            "last_name", "first_name", "surname"
        ),
        label="Клиент",
        widget=forms.Select(
            attrs={
                "onchange": "clearFormSet(); this.form.submit();",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not user.is_manager:
            self.fields["client"].queryset = self.fields["client"].queryset.filter(
                prosthetist=user
            )  # .order_by("-client")

        self.fields["client"].empty_label = "---выбрать---"


class ProsthesisSelectForm(forms.ModelForm):
    """
    Форма выбора протеза.
    """

    class Meta:
        model = Job
        fields = ("prosthesis",)

    def __init__(self, job=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if job is not None:
            region = job.client.region
            self.fields["prosthesis"].queryset = Prosthesis.objects.filter(
                region=region
            ).order_by("number")
            self.fields["prosthesis"].empty_label = "---выбрать---"
            self.fields["prosthesis"].initial = job.prosthesis


class ClientJobsSelectForm(forms.ModelForm):
    """
    Форма выбора работы клиента.
    """

    class Meta:
        model = Job
        fields = ("prosthesis",)

    def __init__(self, job=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if job is not None:
            region = job.client.region
            self.fields["prosthesis"].queryset = Prosthesis.objects.filter(
                region=region
            ).order_by("number")
            self.fields["prosthesis"].empty_label = "---выбрать---"
            self.fields["prosthesis"].initial = job.prosthesis


class PickPartForm(forms.Form):
    """
    Форма выбора комплектующей в протез.
    """

    part = forms.ModelChoiceField(queryset=Part.objects.all(), label="Артикул")
    quantity = forms.IntegerField(
        label="Количество",
        required=True,
        min_value=0,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        part_field = self.fields["part"]
        part_field.empty_label = "---выбрать---"
        part_field.queryset = part_field.queryset.order_by("vendor_code")
        self.fields["quantity"].widget.attrs["class"] = "text-center"


PickPartsFormSet = forms.formset_factory(form=PickPartForm, extra=1)


class PartAddForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = (
            "vendor_code",
            "name",
            "units",
            "price",
            "manufacturer",
            "note",
        )


PartAddFormSet = forms.modelformset_factory(
    model=Part,
    extra=1,
    exclude=("id",),
)


class CommentForm(forms.Form):
    comment = forms.CharField(
        label="Комментарий",
        max_length=1024,
        required=False,
        widget=forms.Textarea(attrs={"cols": 80, "rows": 2}),
    )


class FreeOrderForm(ItemForm):
    """
    Форма свободного заказа.
    """

    minimum_remainder = forms.ChoiceField(
        label="Неснижаемый остаток",
        choices=(),
        required=False,
        initial="-",
        widget=forms.Select(
            attrs={
                "disabled": "true",
                "class": "text-center",
                "style": "-webkit-appearance: none;",
            }
        ),
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = self.fields["part"].queryset
        self.fields["minimum_remainder"].choices = [(0, "-")] + list(
            queryset.values_list("id", "minimum_remainder")
        )

    class Meta:
        model = Item
        fields = ("part", "quantity", "minimum_remainder")


FreeOrderFormSet = forms.formset_factory(FreeOrderForm, extra=1)


class ReceptionForm(forms.ModelForm):
    # invoice_number = forms.ChoiceField(
    #     label="Номер счёта",
    #     queryset=Order.objects.filter(
    #         items__arrived=False,
    #         is_current=False,
    #         invoice_number__isnull=False,
    #     ).distinct(),
    # )

    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.filter(
            order__is_current=False, items__arrived=False
        ).distinct(),
        label="Номер счёта",
        widget=forms.Select(
            attrs={
                "onchange": "clearFormSet(); this.form.submit();",
            }
        ),
    )

    class Meta(InventoryLogFormMeta):
        fields = ["invoice", "comment", "date"]


class InvoiceNumberForm(forms.Form):
    part_id = forms.CharField(required=False)
    invoice_number = forms.CharField(max_length=100, required=False)


InvoiceNumberFormSet = forms.formset_factory(InvoiceNumberForm, extra=0)


class ProsthesisForm(forms.ModelForm):
    class Meta:
        model = Prosthesis
        fields = "__all__"
        widgets = {
            "price_start_date": DatePicker(format="%Y-%m-%d"),
            "price_end_date": DatePicker(format="%Y-%m-%d"),
        }
