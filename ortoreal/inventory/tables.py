from django.conf import settings

import django_tables2 as tables

from inventory.models import InventoryLog, Item
from inventory.utils import dec2pre

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
            "td": {
                "class": "text-center",
            },
            "tfoot": {
                "class": "text-end",
            },
        }


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


class InventoryLogsTable(tables.Table):
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
    def render_warehouse(self, record):
        return record.get_warehouse_display()

    class Meta:
        model = Item
        template_name = "django_tables2/bootstrap5.html"
