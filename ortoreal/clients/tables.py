from django.conf import settings
from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe

import django_tables2 as tables

from clients.models import Client, Job
from inventory.models import InventoryLog, Item
from inventory.utils import dec2pre, get_dec_display

# class ClientsTable(tables.Table):
#     initials = tables.Column("Пр-т", accessor="prosthetist.initials")
#     items = tables.Column("Комплектующие")

#     def wrap_in_color(self, string, color):
#         colors = {
#             "red": "lightcoral",
#             "blue": "mediumturquoise",
#             "green": "lightgreen",
#         }
#         if color in colors:
#             return (
#                 f'<span style="background: {colors[color]}; padding: 2px;'
#                 f'border-radius: 2px;">{string}</span>'
#             )

#     def render_items(self, record):
#         records = record.reserved_items.annotate(
#             item_status=Case(
#                 When(
#                     warehouse__isnull=False,
#                     then=Concat(Value("(С"), F("warehouse"), Value(")")),
#                 ),
#                 When(order__current=False, then=Value("(З)")),
#                 default=Value("(T)"),
#                 output_field=models.CharField(),
#             ),
#             color=Case(
#                 When(
#                     warehouse__isnull=False,
#                     then=Value("green"),
#                 ),
#                 When(order__current=False, then=Value("blue")),
#                 default=Value("red"),
#                 output_field=models.CharField(),
#             ),
#             status=Concat(
#                 F("part__vendor_code"), Value(" "), F("item_status")
#             ),
#         ).order_by("part__vendor_code", F("warehouse").desc(nulls_last=True))
#         result = ""
#         n = 6
#         for i in range(len(records) // n + 1):
#             offset = i * n
#             line = []
#             for item in records[offset : offset + n]:
#                 line.append(self.wrap_in_color(item.status, item.color))
#             result += " ".join(line)
#             # вставляем разделение
#             if offset + n - 1 < len(records):
#                 result += '<hr style="color: transparent;margin: 1px 0;">'

#         return mark_safe(result)

#     def render_status(self, record, column):
#         status_colors = {
#             "in work": "B6D7A8",
#             "issued": "6AA84F",
#             "docs submitted": "34A853",
#             "payment to client": "00FFFF",
#             "payment": "6D9EEB",
#         }
#         # задаём цвет статуса
#         if record.status in status_colors:
#             print("here")
#             color = status_colors[record.status]
#             column.attrs = {"td": {"style": f"background: #{color};"}}
#         # вставляем перенос строки между статусом и датой статуса
#         return mark_safe("<br/>".join(record.status_display.rsplit(" ", 1)))

#     def render_prosthesis(self, record, value):
#         region = "МО"
#         if value.region == "Moscow":
#             region = "М"
#         string = " ".join(
#             [region, value.number, "<br/>", get_dec_display(value.price)]
#         )
#         return mark_safe(string)

#     class Meta:
#         model = Job
#         row_attrs = {
#             "data-href": lambda record: record.get_absolute_url,
#             "style": "cursor: pointer;",
#         }
#         sequence = (
#             "id",
#             "client",
#             "initials",
#             "prosthesis",
#             "status",
#             "items",
#         )
#         exclude = ("prosthetist", "date")
#         template_name = "django_tables2/bootstrap5-responsive.html"


# class ClientPartsTable(tables.Table):
#     vendor_code = tables.Column("Артикул", order_by=("vendor_code", "date"))
#     part_name = tables.Column("Наименование", order_by=("part_name", "date"))
#     item_count = tables.Column("Количество", order_by=("item_count", "date"))

#     class Meta:
#         template_name = "django_tables2/bootstrap5-responsive.html"
