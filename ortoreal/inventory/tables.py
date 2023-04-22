from django.conf import settings

import django_tables2 as tables

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


class OrderTable(tables.Table):
    row = tables.Column("№", empty_values=())
    vendor_code = tables.Column("Артикул")
    quantity = tables.Column("Количество")
    vendor = tables.Column("Производитель")
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
