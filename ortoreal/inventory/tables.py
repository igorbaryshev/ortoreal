from django.conf import settings
from django.db import models
from django.db.models import Case, Count, F, Sum, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from clients.models import Job
from clients.tables import ItemsColumn
from inventory.models import InventoryLog, Item, Order, Part, Vendor
from inventory.utils import get_dec_display, wrap_in_color

TD_END = {
    "td": {
        "class": "text-end",
    },
}
TD_CENTER = {
    "td": {
        "class": "text-center",
    },
}


class NomenclatureTable(tables.Table):
    """
    Таблица номенклатуры.
    """

    vendor_code = tables.Column(
        "Артикул", attrs={"td": {"style": "min-width: 18ch;"}}
    )
    quantity = tables.Column("На складе", accessor="items")
    price = tables.Column(
        "Цена, руб.",
        attrs={"td": {"class": "text-end", "style": "min-width: 11ch;"}},
    )
    name = tables.Column(
        "Наименование",
        attrs={"td": {"style": "width: 90ch; min-width: 20ch;"}},
    )
    minimum_remainder = tables.Column(
        "Неснижаемый остаток", attrs={"td": {"style": "width: 4ch;"}}
    )

    def render_quantity(self, record):
        quantity = record.items.filter(job=None, arrived=True).count()
        units = record.units or ""
        return f"{quantity} {units}"

    def render_price(self, value):
        return get_dec_display(value)

    class Meta:
        model = Part
        orderable = True
        sequence = (
            "id",
            "vendor_code",
            "name",
            "price",
            "manufacturer",
            "vendor",
            "note",
            "minimum_remainder",
            "quantity",
        )
        exclude = ("units",)
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class PartItemsTable(tables.Table):
    """
    Таблица комплектующих на складе.
    """

    vendor_code = tables.Column(
        "Артикул",
        accessor="part.vendor_code",
        attrs={"td": {"style": "min-width: 18ch;"}},
    )
    name = tables.Column(
        "Наименование",
        accessor="part.name",
        attrs={"td": {"style": "width: 90ch; min-width: 20ch;"}},
    )
    price = tables.Column(
        "Цена, руб.",
        attrs={"td": {"class": "text-end", "style": "min-width: 11ch;"}},
    )
    manufacturer = tables.Column("Производитель", accessor="part.manufacturer")
    vendor = tables.Column("Поставщик", accessor="part.vendor")

    def render_price(self, value):
        return get_dec_display(value)

    def render_vendor(self, record, value):
        if record.vendor2:
            return 2
        return value

    def order_vendor(self, queryset, is_descending):
        vendor2 = Vendor.objects.get(name="2")
        queryset = queryset.annotate(
            vendor=Case(
                When(vendor2=True, then=Value(vendor2.name)),
                default=F("part__vendor__name"),
            )
        ).order_by(("-" if is_descending else "") + "vendor")
        return (queryset, True)

    class Meta:
        model = Item
        orderable = True
        sequence = (
            "id",
            "vendor_code",
            "name",
            "price",
            "job",
            "reserved",
            "order",
            "date",
            "free_order",
            "manufacturer",
            "vendor",
        )
        exclude = ("part", "vendor2")
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class VendorExportTable(tables.Table):
    """
    Таблица для экпорта.
    """

    row = tables.Column("№", empty_values=())
    vendor_code = tables.Column("Артикул")
    quantity = tables.Column("Количество")


class VendorOrderTable(tables.Table):
    row = tables.Column("№", empty_values=())
    vendor_code = tables.Column("Артикул")
    quantity = tables.Column("Количество")
    price = tables.Column(
        "Примерная цена, руб.", attrs=TD_END, footer="Всего:"
    )
    price_mul = tables.Column(
        "Всего, руб.",
        footer=lambda table: get_dec_display(
            sum(x["price_mul"] for x in table.data)
        ),
        attrs=TD_END,
    )

    def render_price(self, value):
        return get_dec_display(value)

    def render_price_mul(self, value):
        # Конвертация суммы из аннотированного сета
        # в сумму с двумя знаками после запятой
        return get_dec_display(value)

    class Meta:
        orderable = False
        attrs = settings.DJANGO_TABLES2_TABLE_ATTRS | {
            "th": {
                "class": "text-center",
            },
            # "td": {
            #     "class": "text-center",
            # },
            "tfoot": {
                "class": "text-end",
            },
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class OrderTable(VendorOrderTable):
    vendor = tables.Column("Поставщик")

    class Meta(VendorOrderTable.Meta):
        sequence = (
            "row",
            "vendor_code",
            "quantity",
            "vendor",
            "price",
            "price_mul",
        )


class OrdersTable(tables.Table):
    """
    Таблица списка заказов.
    """

    parts = tables.Column("Комплектующие", empty_values=())
    total_price = tables.Column("Итоговая цена, руб.", empty_values=())

    def render_date(self, record, value):
        if record.current:
            value = "Текущий"
        return value

    def render_parts(self, record):
        per_line = 6
        separator = "<br/>"
        parts = (
            record.items.values("part")
            .annotate(
                item_count=Count("id"),
                items_filled=Count(Case(When(arrived=True, then=1))),
                color=Case(
                    When(item_count=F("items_filled"), then=Value("green")),
                    When(items_filled=0, then=Value("red")),
                    default=Value("yellow"),
                    output_field=models.CharField(),
                ),
                status=Concat(
                    F("part__vendor_code"),
                    Value(" ("),
                    F("items_filled"),
                    Value("/"),
                    F("item_count"),
                    Value(")"),
                    output_field=models.CharField(),
                ),
            )
            .order_by("part__vendor_code")
        )

        items = []
        for i, part in enumerate(parts):
            content = wrap_in_color(color=part["color"], string=part["status"])
            items.append(content)
            # вставляем разделение
            if ((len(items) + 1) % (per_line + 1) == 0) and (
                i < (len(parts) + 1)
            ):
                items.append(separator)

        return mark_safe(" ".join(items))

    def render_total_price(self, record):
        price = (
            Order.objects.filter(pk=record.pk)
            .annotate(total_price=Sum("items__price"))
            .values_list("total_price", flat=True)[0]
        )
        return get_dec_display(price)

    class Meta:
        orderable = False
        model = Order
        sequence = (
            "id",
            "date",
            "parts",
            "total_price",
        )
        exclude = ("current",)
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class InventoryLogsTable(tables.Table):
    """
    Таблица логов инвентаря.
    """

    vendor_code = tables.Column("Артикул", order_by=("vendor_code", "date"))
    part_name = tables.Column("Наименование", order_by=("part_name", "date"))
    item_count = tables.Column(
        "Количество", order_by=("item_count", "date"), attrs=TD_END
    )

    class Meta:
        model = InventoryLog
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        sequence = (
            "id",
            "operation",
            "vendor_code",
            "part_name",
            "item_count",
            "job",
            "prosthetist",
            "date",
            "comment",
        )
        exclude = ("part",)
        template_name = "django_tables2/bootstrap5-responsive.html"


class InventoryLogItemsTable(tables.Table):
    """
    Таблица комплектующих в записи инвентаря.
    """

    class Meta:
        model = Item
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        template_name = "django_tables2/bootstrap5.html"


class JobSetsTable(tables.Table):
    """
    Таблица комплектов протезов.
    """

    reserved_items = ItemsColumn(
        verbose_name="Комплектующие", separator="<br/>", per_line=10
    )
    client = tables.Column(
        "Клиент", linkify=lambda record: record.client.get_absolute_url()
    )
    status = tables.Column("Статус", empty_values=())

    def render_status(self, record, column):
        status_colors = {
            "in work": "B6D7A8",
            "issued": "6AA84F",
            "docs submitted": "34A853",
            "payment to client": "00FFFF",
            "payment": "6D9EEB",
        }
        # задаём цвет статуса
        if not record.statuses.exists():
            return record.status_display
        status = record.statuses.latest("date").name
        if status in status_colors:
            color = status_colors[status]
            column.attrs = {"td": {"style": f"background: #{color};"}}
        # вставляем перенос строки между статусом и датой статуса
        # rsplit разделяет с конца
        return mark_safe("<br/>".join(record.status_display.rsplit(" ", 1)))

    def render_prosthesis(self, value):
        region = "МО"
        if value.region == "Moscow":
            region = "М"
        string = " ".join(
            [region, value.number, "<br/>", get_dec_display(value.price)]
        )
        return mark_safe(string)

    class Meta:
        model = Job
        sequence = (
            "id",
            "client",
            "prosthetist",
            "prosthesis",
            "status",
            "reserved_items",
        )
        exclude = ("date", "items")
        row_attrs = {
            "data-href": lambda record: reverse(
                "inventory:job_set", kwargs={"pk": record.pk}
            ),
            "style": "cursor: pointer;",
        }


class JobPartsTable(tables.Table):
    """
    Таблица комплектующих в комплекте.
    """

    vendor_code = tables.Column("Артикул", order_by=("vendor_code", "date"))
    part_name = tables.Column("Наименование", order_by=("part_name", "date"))
    item_count = tables.Column("Количество", order_by=("item_count", "date"))

    class Meta:
        template_name = "django_tables2/bootstrap5-responsive.html"


class MarginTable(tables.Table):
    """
    Таблица маржи.
    """

    region = tables.Column("Регион", accessor="prosthesis.region")
    price = tables.Column("Цена", attrs=TD_END)
    price_items = tables.Column("Комплектующие", attrs=TD_END)
    margin = tables.Column("Маржа", attrs=TD_END)
    status = tables.Column("Статус", attrs=TD_END, accessor="status_display")

    def render_price(self, value):
        return get_dec_display(value)

    def render_price_items(self, value):
        return get_dec_display(value)

    def render_margin(self, value):
        return get_dec_display(value)

    class Meta:
        model = Job
        sequence = (
            "client",
            "prosthetist",
            "prosthesis",
            "date",
            "status",
            "region",
            "price",
            "price_items",
            "margin",
        )
        exclude = ("id",)
        template_name = "django_tables2/bootstrap5-responsive.html"


class ClientItemsTable(PartItemsTable):
    """
    Таблица комплектующих записанных в резерв для протеза клиента.
    """

    class Meta:
        model = Item
        orderable = True
        sequence = (
            "id",
            "vendor_code",
            "name",
            "price",
            "order",
            "date",
            "manufacturer",
        )
        exclude = (
            "vendor2",
            "free_order",
            "reserved",
            "job",
            "vendor",
            "part",
        )
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"
