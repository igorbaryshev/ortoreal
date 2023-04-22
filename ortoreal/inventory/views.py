from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber

import django_tables2 as tables
from django_tables2.export.views import ExportMixin

from inventory.forms import (
    InventoryAddForm,
    InventoryTakeForm,
    ItemAddFormSet,
    ItemTakeFormSet,
    PartAddFormSet,
)
from inventory.models import Item, InventoryLog, Part, Order
from inventory.tables import OrderTable


def parts(request):
    table_head = Part.get_field_names() + [
        "Склад 1",
        "Склад 2",
        "Всего",
        "Единицы",
    ]
    parts_list = Part.objects.prefetch_related("items")
    paginator = Paginator(parts_list, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "table_head": table_head,
        "page_obj": page_obj,
    }

    return render(request, "inventory/parts.html", context)


def items(request, pk):
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
    entry_form = InventoryAddForm(request.POST or None, prefix="entry")
    item_formset = ItemAddFormSet(request.POST or None, prefix="item")

    if (
        request.method == "POST"
        and entry_form.is_valid()
        and item_formset.is_valid()
    ):
        date = entry_form.cleaned_data.get("date")
        operation = entry_form.cleaned_data.get("operation")
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

    return render(request, "inventory/form_table.html", context)


@login_required
def take_items(request):
    entry_form = InventoryTakeForm(request.POST or None, prefix="entry")
    item_formset = ItemTakeFormSet(request.POST or None, prefix="item")

    if (
        request.method == "POST"
        and entry_form.is_valid()
        and item_formset.is_valid()
    ):
        date = entry_form.cleaned_data.get("date")
        operation = InventoryLog.LogAction.TOOK
        comment = entry_form.cleaned_data.get("comment")
        batch_logs = []

        for form in item_formset:
            quantity = form.cleaned_data.get("quantity")
            part = form.cleaned_data.get("part")
            if quantity > int(part.quantity_total):
                raise forms.ValidationError("TOO MANY")
            c2_quantity = int(part.quantity_c2)
            removed = 0
            if c2_quantity >= 1:
                items = (
                    part.items.filter(warehouse="с2")
                    .order_by("date_added")
                    .values_list("pk", flat=True)[:quantity]
                )
                removed = Item.objects.filter(id__in=items).delete()[0]
            c1_quantity = quantity - removed
            if c1_quantity <= int(part.quantity_c1):
                items = (
                    part.items.filter(warehouse="с1")
                    .order_by("date_added")
                    .values_list("pk", flat=True)[:c1_quantity]
                )
                Item.objects.filter(id__in=items).delete()

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

        return redirect("/admin/inventory/inventorylog/")

    context = {
        "form": entry_form,
        "formset": item_formset,
        "taking": True,
    }

    return render(request, "inventory/add_items.html", context)


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
