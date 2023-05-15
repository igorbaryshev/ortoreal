from django import forms
from django.db.models import Count, Q
from django.utils import timezone

from clients.models import Client, Job
from inventory.models import InventoryLog, Item, Part, Prosthesis


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
        queryset=Job.objects.none(),
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
        self.fields["job"].queryset = Job.objects.filter(
            prosthetist=user
        ).order_by("-client")

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
    quantity = forms.IntegerField(
        label="Количество", min_value=0, required=False
    )
    part_id = forms.IntegerField(widget=forms.HiddenInput())


ItemReturnFormSet = forms.formset_factory(
    form=ItemReturnForm,
    extra=0,
)


class JobSelectForm(forms.Form):
    """
    Форма выбора клиента для страницы выбора комплектации.
    """

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

        self.fields["job"].empty_label = "---выбрать---"


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
            ).order_by("name")
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


PickPartsFormSet = forms.formset_factory(form=PickPartForm, extra=1)


class PartAddForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ("vendor_code", "name", "units", "price", "vendor", "note")


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

    class Meta:
        model = Item
        fields = ("part", "quantity")


FreeOrderFormSet = forms.formset_factory(FreeOrderForm, extra=1)
