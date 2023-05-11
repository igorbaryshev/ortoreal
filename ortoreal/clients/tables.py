from django.conf import settings

import django_tables2 as tables

from clients.models import Client, Job
from inventory.models import InventoryLog, Item
from inventory.utils import dec2pre


class ClientsTable(tables.Table):
    class Meta:
        model = Job
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }
        sequence = (
            "client",
            "prosthesis",
        )
        template_name = "django_tables2/bootstrap5-responsive.html"


class ClientPartsTable(tables.Table):
    vendor_code = tables.Column("Артикул", order_by=("vendor_code", "date"))
    part_name = tables.Column("Наименование", order_by=("part_name", "date"))
    item_count = tables.Column("Количество", order_by=("item_count", "date"))

    class Meta:
        template_name = "django_tables2/bootstrap5-responsive.html"
