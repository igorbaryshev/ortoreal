from django.conf import settings
from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.html import conditional_escape, format_html, mark_safe

import django_tables2 as tables
from django_tables2.columns import booleancolumn
from django_tables2.columns.base import LinkTransform, library

from clients.models import Client, Job, Status
from inventory.models import InventoryLog, Item, Part
from inventory.utils import dec2pre, get_dec_display, wrap_in_color

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


# @library.register
class ItemsColumn(tables.ManyToManyColumn):
    def __init__(self, per_line=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.per_line = per_line

    def transform(self, obj):
        status = self.get_status(obj)
        color = self.get_color(obj)
        self.attrs["a"] = wrap_in_color(color, link=True)
        self.linkify_item = LinkTransform(attrs=self.attrs.get("a", {}))
        return status

    def get_color(self, item):
        if item.arrived:
            if item.job is None:
                return "green"
            return "darkgreen"
        if item.order and item.order.is_current:
            return "red"
        return "blue"

    def get_status(self, item):
        status = "(3)"
        if item.arrived:
            if item.job is None:
                status = "(C)"
            else:
                status = "(П)"
        elif item.order and item.order.is_current:
            status = "(T)"
        return item.part.vendor_code + " " + status

    def render(self, value):
        items = []
        filtered_items = self.filter(value)
        for i, item in enumerate(filtered_items):
            content = self.transform(item)
            if hasattr(self, "linkify_item"):
                content = self.linkify_item(content=content, record=item)

            items.append(content)
            if ((len(items) + 1) % (self.per_line + 1) == 0) and (
                i < (len(filtered_items) + 1)
            ):
                items.append(self.separator)

        return mark_safe(" ".join(items))


class ClientProsthesisListTable(tables.Table):
    reserved_items = ItemsColumn(
        verbose_name="Комплектующие", separator="<br/>", per_line=6
    )
    status = tables.Column("Статус", empty_values=())
    price = tables.Column("Цена", accessor="prosthesis.price")
    region = tables.Column("Регион", accessor="prosthesis.region")

    def render_status(self, record, column):
        status = record.statuses.latest("date")
        status_name = "-".join(status.name.split())
        column.attrs = {"td": {"class": status_name}}
        job_url = reverse("clients:change_job_status", kwargs={"pk": record.pk})
        button = f'<a class="btn btn-secondary" href="{job_url}">Изменить</a>'
        return mark_safe(record.status_display + "</br>" + button)

    class Meta:
        model = Job
        sequence = [
            "prosthetist",
            "prosthesis",
            "status",
            "price",
            "region",
            "date",
            "reserved_items",
        ]
        exclude = ["id", "client", "is_finished"]
        row_attrs = {
            # "data-href": lambda record: reverse(
            #     "inventory:job_set", kwargs={"pk": record.pk}
            # ),
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }


# TODO
class StatusesColumn(tables.ManyToManyColumn):
    def __init__(self, per_line=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.per_line = per_line

    def transform(self, obj):
        status = self.get_status(obj)
        color = self.get_color(obj)
        self.attrs["a"] = wrap_in_color(color, link=True)
        self.linkify_item = LinkTransform(attrs=self.attrs.get("a", {}))
        return status

    def get_color(self, item):
        if item.arrived:
            if item.job is None:
                return "green"
            return "darkgreen"
        if item.order and item.order.is_current:
            return "red"
        return "blue"

    def get_status(self, item):
        status = "(3)"
        if item.arrived:
            if item.job is None:
                status = "(C)"
            else:
                status = "(П)"
        elif item.order and item.order.is_current:
            status = "(T)"
        return item.part.vendor_code + " " + status

    def render(self, value):
        items = []
        filtered_items = self.filter(value)
        for i, item in enumerate(filtered_items):
            content = self.transform(item)
            if hasattr(self, "linkify_item"):
                content = self.linkify_item(content=content, record=item)

            items.append(content)
            if ((len(items) + 1) % (self.per_line + 1) == 0) and (
                i < (len(filtered_items) + 1)
            ):
                items.append(self.separator)

        return mark_safe(" ".join(items))


ClientsBooleanColumn = tables.BooleanColumn(yesno="✅,❌", empty_values=())


class ClientsTable(tables.Table):
    latest_job_date = tables.Column("Дата последней работы")
    full_name = tables.Column("ФИО")
    jobs_count = tables.Column("Всего работ", accessor="jobs_count")
    jobs_in_progress = tables.Column("Активные", accessor="jobs_in_progress")
    statuses = tables.Column("Статусы активных работ", empty_values=())
    passport = tables.Column("Паспорт", empty_values=(), accessor="passport")
    bank_details = tables.Column("Реквизиты", empty_values=(), accessor="bank_details")
    snils = tables.Column(empty_values=())
    snils_scan = ClientsBooleanColumn
    ipr = ClientsBooleanColumn
    sprmse = ClientsBooleanColumn

    def get_yesno(self, value):
        if value:
            return "✅"
        return "❌"

    def render_full_name(self, record):
        return str(record)

    def render_snils(self, value):
        if value:
            return value
        return self.get_yesno(value)

    def render_passport(self, value):
        return self.get_yesno(value)

    def render_bank_details(self, value):
        return self.get_yesno(value)

    def render_statuses(self, record, column):
        jobs = record.jobs.filter(is_finished=False).order_by("-date")
        statuses_display = []
        for job in jobs:
            status = job.statuses.latest("date")
            job_name = job.prosthesis or "протез не выбран"
            status_name = "-".join(status.name.split())
            status_display = (
                f'<span class="{status_name} status-pill">'
                f"{job_name} - {status}</span>"
            )
            statuses_display.append(status_display)
        output = "<br>".join(statuses_display)
        return mark_safe(output)

    class Meta:
        model = Client
        orderable = False
        sequence = [
            "id",
            "full_name",
            "jobs_count",
            "jobs_in_progress",
            "statuses",
            "birth_date",
            "phone",
            "address",
            "passport",
            "bank_details",
        ]
        exclude = ["last_name", "first_name", "surname", "prosthetist"]
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }


class JobStatusesTable(tables.Table):
    """
    Таблица статусов работы.
    """

    class Meta:
        model = Status
        sequence = [
            "date",
            "name",
            "comment",
        ]
        exclude = ["color", "id", "job"]
        row_attrs = {
            "data-href": lambda record: record.get_absolute_url,
            "style": "cursor: pointer;",
        }


class JobItemsTable(tables.Table):
    """
    Таблица комплектующих работы.
    """

    part = tables.Column("Артикул", accessor="part.vendor_code")
    status = tables.Column("Статус", accessor="status")

    class Meta:
        model = Item
        sequence = [
            "part",
            "date",
            "order",
            "invoice",
            "status",
        ]
        exclude = [
            "id",
            "arrived",
            "vendor2",
            "job",
            "reserved",
            "price",
            "free_order",
        ]
