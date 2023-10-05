from decimal import Decimal

from django import forms
from django.db.models import Case, F, Q, Sum, Value, When
from django.db.models.functions import Concat
from django.utils import timezone

import django_filters as filters
from bootstrap_datepicker_plus.widgets import (
    DatePickerInput,
    DateTimePickerInput,
)
from django_filters import FilterSet, widgets
from django_select2 import forms as s2forms

from clients.models import Job
from inventory.forms import DatePicker
from inventory.models import InventoryLog, Part


def get_current_date():
    return timezone.localtime().strftime("%Y-%m-%d %H:%M")


def get_first_job_date():
    if not Job.objects.exists():
        return get_current_date()
    date = Job.objects.earliest("date").date
    return timezone.localtime(date).strftime("%Y-%m-%d %H:%M")


class JobWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "client__first_name__icontains",
        "client__last_name__icontains",
    ]


class InventoryLogFilter(FilterSet):
    job = filters.CharFilter(
        label="Работа",
        field_name="job",
        lookup_expr="client__last_name__istartswith",
    )
    vendor_code = filters.CharFilter(
        label="Артикул", field_name="vendor_code", lookup_expr="istartswith"
    )
    part_name = filters.CharFilter(
        label="Название компл.",
        field_name="part_name",
        lookup_expr="icontains",
    )
    invoice_number = filters.CharFilter(
        label="Номер счёта",
        field_name="invoice",
        lookup_expr="number__istartswith",
    )
    invoice_vendor = filters.CharFilter(
        label="Поставщик",
        field_name="invoice",
        lookup_expr="order__vendor__name__istartswith",
    )
    start_date = filters.DateTimeFilter(
        label="От",
        field_name="date",
        lookup_expr=("gte"),
        widget=DatePicker(attrs={"value": get_first_job_date}),
    )
    end_date = filters.DateTimeFilter(
        label="До",
        field_name="date",
        lookup_expr=("lte"),
        widget=DatePicker(attrs={"value": get_current_date}),
    )

    class Meta:
        model = InventoryLog
        fields = ["operation", "job", "prosthetist"]


class PartFilter(FilterSet):
    price__gte = filters.NumberFilter(
        label="от, руб.", field_name="price", lookup_expr="gte"
    )
    price__lte = filters.NumberFilter(
        label="до, руб.", field_name="price", lookup_expr="lte"
    )

    class Meta:
        model = Part
        fields = {
            "vendor_code": ["icontains"],
            "name": ["icontains"],
            "manufacturer": ["exact"],
            "price": [],
        }


class MarginFilter(FilterSet):
    """
    Фильтр для страницы Маржи.

        Фильтрует по дате от и до,
        по протезисту из списка
        и по полному имени пациента.
    """

    start_date = filters.DateFilter(
        label="От",
        field_name="date",
        lookup_expr=("gte"),
        widget=DatePicker(attrs={"value": get_first_job_date}),
    )
    end_date = filters.DateFilter(
        label="До",
        field_name="date",
        lookup_expr=("lte"),
        widget=DatePicker(attrs={"value": get_current_date}),
    )
    full_name = filters.CharFilter(
        label="Имя клиента",
        field_name="full_name",
        method="search_by_full_name",
    )

    def search_by_full_name(self, qs, name, value):
        """
        Поиск по полному имени, порядок ФИО неважен.
        """
        # Записываем первое значение, а остальные идут в массив
        first_name, *last_name = value.split()
        qs = qs.order_by("-date")
        qs = qs.annotate(
            # Создаём поле с полным именем, где отчество опционально
            full_name=Concat(
                F("client__last_name"),
                Value(" "),
                F("client__first_name"),
                Case(
                    When(
                        client__surname__isnull=False,
                        then=Concat(Value(" "), F("client__surname")),
                    ),
                    default=Value(""),
                ),
            )
        ).filter(full_name__icontains=first_name)

        # Если в массиве нет значений, то возвращаем полученный QuerySet
        if not last_name:
            return qs

        qs = qs.filter(full_name__icontains=last_name[0])

        # Если нет третьего значения, то возвращаем QuerySet по двум первым
        if len(last_name) == 1:
            return qs

        qs = qs.filter(full_name__icontains=last_name[1])
        return qs

    class Meta:
        model = Job
        fields = ["start_date", "end_date", "prosthetist"]
