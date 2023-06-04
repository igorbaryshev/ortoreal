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

from clients.models import Job
from inventory.forms import DatePicker
from inventory.models import Part


def get_current_date():
    return timezone.now().date()


def get_first_job_date():
    if not Job.objects.exists():
        return get_current_date()
    return Job.objects.earliest("date").date.strftime("%Y-%m-%d")


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
        fields = ("start_date", "end_date", "prosthetist")
