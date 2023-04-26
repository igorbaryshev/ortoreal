import io
import urllib

import django_tables2 as tables
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_tables2.export.views import ExportMixin

from clients.models import Client, Job
from inventory.forms import (
    InventoryAddForm,
    InventoryTakeForm,
    ItemAddFormSet,
    ItemTakeFormSet,
    PartAddFormSet,
    ItemReturnForm,
)
from inventory.models import InventoryLog, Item, Order, Part
from inventory.tables import OrderTable, VendorOrderTable
from inventory.utils import generate_zip, is_prosthetist
from xlsxwriter.workbook import Workbook

PARTS_PER_PAGE = 20


def nomenclature(request):
    """
    Номенклатура.
    """
    table_head = Part.get_field_names() + [
        "Склад 1",
        "Склад 2",
        "Всего",
        "Единицы",
    ]
    parts_list = Part.objects.order_by("vendor_code").prefetch_related("items")
    paginator = Paginator(parts_list, PARTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "table_head": table_head,
        "page_obj": page_obj,
    }

    return render(request, "inventory/nomenclature.html", context)


def items(request, pk):
    """
    Список комплектующих на складе.
    """
    part = get_object_or_404(Part, pk=pk)
    items_list = part.items.order_by("id")
    table_head = ["ID"] + Item.get_field_names()[2:]
    paginator = Paginator(items_list, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "part": part,
        "table_head": table_head,
        "page_obj": page_obj,
    }

    return render(request, "inventory/items.html", context)


@login_required
def add_items(request):
    """
    Приход.
    """
    entry_form = InventoryAddForm(request.POST or None, prefix="entry")
    item_formset = ItemAddFormSet(request.POST or None, prefix="item")

    if (
        request.method == "POST"
        and entry_form.is_valid()
        and item_formset.is_valid()
    ):
        date = entry_form.cleaned_data.get("date")
        operation = InventoryLog.LogAction.RECEIVED
        comment = entry_form.cleaned_data.get("comment")
        batch_items = []
        batch_logs = []
        for form in item_formset:
            quantity = form.cleaned_data.get("quantity")
            if quantity:
                part = form.cleaned_data.get("part")
                warehouse = form.cleaned_data.get("warehouse")
                batch_items += [
                    Item(part=part, warehouse=warehouse, date_added=date)
                    for _ in range(quantity)
                ]
                log = InventoryLog(
                    operation=operation,
                    comment=comment,
                    part=part,
                    added_by=request.user,
                    date=date,
                    quantity=quantity,
                )
                batch_logs.append(log)
        InventoryLog.objects.bulk_create(batch_logs)
        Item.objects.bulk_create(batch_items)

        return redirect("admin:inventory_inventorylog_changelist")

    context = {
        "form": entry_form,
        "formset": item_formset,
        "adding": True,
    }
    print(item_formset[0]["part"].name)

    return render(request, "inventory/add_items.html", context)


# @login_required
# @is_prosthetist
# def take_items(request):
#     """
#     Расход/возврат.
#     """
#     entry_form = InventoryTakeForm(request.POST or None, prefix="entry")
#     entry_form.fields["client"].queryset = Client.objects.filter(
#         prosthetist=request.user
#     )
#     item_formset = ItemTakeFormSet(request.POST or None, prefix="item")
#
#     if (
#         request.method == "POST"
#         and entry_form.is_valid()
#         and item_formset.is_valid()
#     ):
#         date = entry_form.cleaned_data.get("date")
#         operation = entry_form.cleaned_data.get("operation")
#         comment = entry_form.cleaned_data.get("comment")
#         batch_logs = []
#
#         for form in item_formset:
#             quantity = form.cleaned_data.get("quantity")
#             part = form.cleaned_data.get("part")
#             if quantity > int(part.quantity_total):
#                 raise forms.ValidationError("TOO MANY")
#             c2_quantity = int(part.quantity_c2)
#             removed = 0
#             if c2_quantity >= 1:
#                 items = (
#                     part.items.filter(warehouse="с2")
#                     .order_by("date_added")
#                     .values_list("pk", flat=True)[:quantity]
#                 )
#                 removed = Item.objects.filter(id__in=items).delete()[0]
#             c1_quantity = quantity - removed
#             if c1_quantity <= int(part.quantity_c1):
#                 items = (
#                     part.items.filter(warehouse="с1")
#                     .order_by("date_added")
#                     .values_list("pk", flat=True)[:c1_quantity]
#                 )
#                 Item.objects.filter(id__in=items).delete()
#
#             log = InventoryLog(
#                 operation=operation,
#                 comment=comment,
#                 part=part,
#                 added_by=request.user,
#                 date=date,
#                 quantity=quantity,
#             )
#             batch_logs.append(log)
#         InventoryLog.objects.bulk_create(batch_logs)
#
#         return redirect("/admin/inventory/inventorylog/")
#
#     context = {
#         "form": entry_form,
#         "formset": item_formset,
#         "taking": True,
#     }
#
#     return render(request, "inventory/take_items.html", context)


@login_required
@is_prosthetist
def take_items(request):
    """
    Расход/возврат.
    """
    entry_form = InventoryTakeForm(request.POST or None, prefix="entry")
    entry_form.fields["client"].queryset = Job.objects.filter(
        prosthetist=request.user
    )
    item_formset = ItemTakeFormSet(request.POST or None, prefix="item")
    ItemReturnFormSet = forms.formset_factory(form=ItemReturnForm, extra=1)
    return_formset = ItemReturnFormSet(request.POST or None, prefix="return")
    context = {
        "form": entry_form,
        "item_formset": item_formset,
        "return_formset": return_formset,
        "taking": True,
    }

    if request.method == "POST":
        if entry_form.is_valid():
            job = entry_form.cleaned_data["client"]
            queryset = job.items.annotate(quantity=Count("part__vendor_code"))
            print(queryset)
            return_formset = ItemReturnFormSet(
                request.POST, prefix="return"
            )
            print(return_formset)
            context["return_formset"] = return_formset
            context["taking"] = True

        # if entry_form.is_valid():
        #     operation = entry_form.cleaned_data.get("operation")
        #     comment = entry_form.cleaned_data.get("comment")
        #     batch_logs = []
    #
    #     for form in item_formset:
    #         quantity = form.cleaned_data.get("quantity")
    #         part = form.cleaned_data.get("part")
    #         if quantity > int(part.quantity_total):
    #             raise forms.ValidationError("TOO MANY")
    #         c2_quantity = int(part.quantity_c2)
    #         removed = 0
    #         if c2_quantity >= 1:
    #             items = (
    #                 part.items.filter(warehouse="с2")
    #                 .order_by("date_added")
    #                 .values_list("pk", flat=True)[:quantity]
    #             )
    #             removed = Item.objects.filter(id__in=items).delete()[0]
    #         c1_quantity = quantity - removed
    #         if c1_quantity <= int(part.quantity_c1):
    #             items = (
    #                 part.items.filter(warehouse="с1")
    #                 .order_by("date_added")
    #                 .values_list("pk", flat=True)[:c1_quantity]
    #             )
    #             Item.objects.filter(id__in=items).delete()
    #
    #         log = InventoryLog(
    #             operation=operation,
    #             comment=comment,
    #             part=part,
    #             added_by=request.user,
    #             date=date,
    #             quantity=quantity,
    #         )
    #         batch_logs.append(log)
    #     InventoryLog.objects.bulk_create(batch_logs)
    #
    #     return redirect("/admin/inventory/inventorylog/")

    return render(request, "inventory/take_items.html", context)


@login_required
def add_parts(request):
    part_formset = PartAddFormSet(request.POST or None, prefix="item")

    if request.method == "POST" and part_formset.is_valid():
        for form in part_formset:
            if form.is_valid():
                form.save()

        return redirect("/admin/inventory/")

    context = {
        "formset": part_formset,
        "adding": True,
    }

    return render(request, "inventory/add_items.html", context)


@login_required
def order(request, pk=None):
    queryset = Order.objects.get(current=True)

    if pk:
        queryset = get_object_or_404(Order, pk=pk)

    table_queryset = (
        queryset.items.values(
            "part__vendor_code", "part__price", "part__vendor"
        )
        .annotate(
            row=Window(RowNumber()),
            vendor_code=F("part__vendor_code"),
            price=F("part__price"),
            quantity=Count("vendor_code"),
            vendor=F("part__vendor__name"),
            price_mul=F("quantity") * F("price"),
        )
        .order_by("vendor_code")
    )
    table = OrderTable(table_queryset)
    context = {
        "table": table,
    }

    return render(request, "inventory/order.html", context)


class OrderView(ExportMixin, tables.SingleTableView):
    table_class = OrderTable
    template_name = "inventory/order.html"

    @property
    def is_current(self):
        if self.kwargs.get("pk"):
            return False
        return True

    def get_order(self):
        if self.is_current:
            return get_object_or_404(Order, current=True)
        return get_object_or_404(Order, pk=self.kwargs.get("pk"))

    def post(self, request):
        if self.is_current:
            order = get_object_or_404(Order, current=True)
            order.current = False
            order.save()
            Order.objects.create()
            return redirect("inventory:order_by_id", pk=order.pk)

    def get_queryset(self):
        order = self.get_order()

        queryset = (
            order.items.values(
                "part__vendor_code", "part__price", "part__vendor"
            )
            .annotate(
                row=Window(RowNumber()),
                vendor_code=F("part__vendor_code"),
                price=F("part__price"),
                quantity=Count("vendor_code"),
                vendor=F("part__vendor__name"),
                price_mul=F("quantity") * F("price"),
            )
            .order_by("vendor_code")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current"] = self.is_current
        return context


def export_orders(request):
    queryset = Order.objects.get(current=True)
    vendors = queryset.items.values_list(
        "part__vendor__id", "part__vendor__name"
    ).distinct()
    table_queryset = (
        queryset.items.values("part__vendor_code", "part__price")
        .annotate(
            row=Window(RowNumber()),
            vendor_code=F("part__vendor_code"),
            price=F("part__price"),
            quantity=Count("vendor_code"),
            price_mul=F("quantity") * F("price"),
        )
        .order_by("vendor_code")
    )
    files = []
    for vendor in vendors:
        vendor_queryset = table_queryset.filter(part__vendor_id=vendor[0])
        table = VendorOrderTable(vendor_queryset)
        output = io.BytesIO()
        workbook = Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()
        for i, row in enumerate(table.as_values()):
            for j, value in enumerate(row):
                worksheet.write(i, j, value)
        worksheet.autofit()
        workbook.close()
        table_file = output.getvalue()
        output.close()
        files.append((vendor[1] + ".xlsx", table_file))

    current_date = timezone.now().strftime("%Y-%m-%d_%H-%M")
    zip_name = urllib.parse.quote(f"Заказ_{current_date}")
    response = HttpResponse(generate_zip(files))
    response["Content-Type"] = "application/x-zip-compressed"
    response[
        "Content-Disposition"
    ] = f"attachment; filename*=UTF-8''{zip_name}.zip"

    return response
