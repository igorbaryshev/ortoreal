from django.conf import settings
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from clients.models import Client, Job
from inventory.models import InventoryLog, Item, Order
from inventory.utils import dec2pre, get_dec_display, wrap_in_color

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
    price = tables.Column("Цена, руб.", attrs=TD_END, footer="Всего:")
    price_mul = tables.Column(
        "Всего, руб.",
        footer=lambda table: dec2pre(sum(x["price_mul"] for x in table.data)),
        attrs=TD_END,
    )

    def render_price_mul(self, value):
        # Конвертация суммы из аннотированного сета
        # в сумму с двумя знаками после запятой
        return dec2pre(value)

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
    vendor = tables.Column("Производитель")

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
        parts = (
            record.items.values("part")
            .annotate(
                item_count=Count("id"),
                items_filled=Count(
                    Case(
                        When(warehouse__isnull=False, then=1),
                        output_field=models.IntegerField(),
                    )
                ),
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
        result = ""
        n = 7
        for i in range(len(parts) // n + 1):
            offset = i * n
            line = []
            for part in parts[offset : offset + n]:
                line.append(wrap_in_color(part["status"], part["color"]))
            result += " ".join(line)
            # вставляем разделение
            if offset + n - 1 < len(parts):
                result += '<hr style="color: transparent;margin: 1px 0;">'

        return mark_safe(result)

    def render_total_price(self, record):
        price = (
            Order.objects.filter(pk=record.pk)
            .annotate(total_price=Sum("items__part__price"))
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
    item_count = tables.Column("Количество", order_by=("item_count", "date"))

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

    def render_warehouse(self, record):
        return record.get_warehouse_display()

    class Meta:
        model = Item
        template_name = "django_tables2/bootstrap5.html"


class JobSetsTable(tables.Table):
    """
    Таблица комплектов протезов.
    """

    initials = tables.Column("Пр-т", accessor="prosthetist.initials")
    items = tables.Column("Комплектующие")

    def wrap_in_color(self, string, color):
        colors = {
            "red": "lightcoral",
            "blue": "mediumturquoise",
            "green": "lightgreen",
        }
        if color in colors:
            return (
                f'<span style="background: {colors[color]}; padding: 2px;'
                f'border-radius: 2px;">{string}</span>'
            )

    def render_items(self, record):
        items = record.reserved_items.annotate(
            item_status=Case(
                When(
                    warehouse__isnull=False,
                    then=Concat(Value("(С"), F("warehouse"), Value(")")),
                ),
                When(order__current=False, then=Value("(З)")),
                default=Value("(T)"),
                output_field=models.CharField(),
            ),
            color=Case(
                When(
                    warehouse__isnull=False,
                    then=Value("green"),
                ),
                When(order__current=False, then=Value("blue")),
                default=Value("red"),
                output_field=models.CharField(),
            ),
            status=Concat(
                F("part__vendor_code"), Value(" "), F("item_status")
            ),
        ).order_by("part__vendor_code", F("warehouse").desc(nulls_last=True))
        result = ""
        n = 6
        for i in range(len(items) // n + 1):
            offset = i * n
            line = []
            for item in items[offset : offset + n]:
                line.append(wrap_in_color(item.status, item.color))
            result += " ".join(line)
            # вставляем разделение
            if offset + n - 1 < len(items):
                result += '<hr style="color: transparent;margin: 1px 0;">'

        return mark_safe(result)

    def render_status(self, record, column):
        status_colors = {
            "in work": "B6D7A8",
            "issued": "6AA84F",
            "docs submitted": "34A853",
            "payment to client": "00FFFF",
            "payment": "6D9EEB",
        }
        # задаём цвет статуса
        if record.status in status_colors:
            print("here")
            color = status_colors[record.status]
            column.attrs = {"td": {"style": f"background: #{color};"}}
        # вставляем перенос строки между статусом и датой статуса
        return mark_safe("<br/>".join(record.status_display.rsplit(" ", 1)))

    def render_prosthesis(self, record, value):
        region = "МО"
        if value.region == "Moscow":
            region = "М"
        string = " ".join(
            [region, value.number, "<br/>", get_dec_display(value.price)]
        )
        return mark_safe(string)

    class Meta:
        model = Job
        row_attrs = {
            "data-href": lambda record: reverse(
                "inventory:job_set", kwargs={"pk": record.pk}
            ),
            "style": "cursor: pointer;",
        }
        sequence = (
            "id",
            "client",
            "initials",
            "prosthesis",
            "status",
            "items",
        )
        exclude = ("prosthetist", "date")
        template_name = "django_tables2/bootstrap5-responsive.html"


class JobPartsTable(tables.Table):
    """
    Таблица комплектующих в комплекте.
    """

    vendor_code = tables.Column("Артикул", order_by=("vendor_code", "date"))
    part_name = tables.Column("Наименование", order_by=("part_name", "date"))
    item_count = tables.Column("Количество", order_by=("item_count", "date"))

    class Meta:
        template_name = "django_tables2/bootstrap5-responsive.html"
