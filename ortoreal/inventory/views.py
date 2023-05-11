import io
import urllib
from typing import Any, Dict, Optional

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, QuerySet, Value, Window
from django.db.models.functions import Concat, RowNumber
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic.list import ListView

import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.paginators import LazyPaginator
from xlsxwriter.workbook import Workbook

from clients.models import Client, Job
from inventory.forms import (
    CommentForm,
    FreeOrderFormSet,
    InventoryAddForm,
    InventoryTakeForm,
    ItemAddFormSet,
    ItemReturnFormSet,
    ItemTakeFormSet,
    JobSelectForm,
    PartAddFormSet,
    PickPartsFormSet,
    ProsthesisSelectForm,
)
from inventory.models import InventoryLog, Item, Order, Part, Prosthesis
from inventory.tables import (
    InventoryLogItemsTable,
    InventoryLogsTable,
    OrderTable,
    VendorOrderTable,
)
from inventory.utils import (
    create_reserve,
    generate_zip,
    is_prosthetist,
    recalc_reserves,
    remove_reserve,
)

PARTS_PER_PAGE = 30


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


class AddItemsView(LoginRequiredMixin, View):
    """
    Приход.
    """

    def get(self, request, *args, **kwargs):
        form = InventoryAddForm(prefix="entry")
        formset = ItemAddFormSet(prefix="item")
        context = {
            "form": form,
            "formset": formset,
            "adding": True,
        }
        return render(request, "inventory/add_items.html", context)

    def post(self, request, *args, **kwargs):
        form = InventoryAddForm(data=request.POST, prefix="entry")
        formset = ItemAddFormSet(data=request.POST, prefix="item")
        if form.is_valid() and formset.is_valid() and formset.forms:
            date = form.cleaned_data["date"]
            operation = InventoryLog.Operation.RECEPTION
            comment = form.cleaned_data["comment"]
            # фильтр: не назначен склад, не в текущем заказе,
            # сортировка по дате резерва, без резерва - в последнюю очередь
            ordered_items = Item.objects.filter(
                warehouse="", order__current=False
            ).order_by(F("reserved__date").asc(nulls_last=True), F("id").asc())
            for formset_form in formset:
                quantity = formset_form.cleaned_data["quantity"]
                # Если кол-во не указано или <= 0, то пропустить
                if quantity is None or quantity <= 0:
                    continue
                log = InventoryLog(
                    operation=operation,
                    comment=comment,
                )
                log.save()
                log = InventoryLog.objects.get(id=log.id)
                part = formset_form.cleaned_data["part"]
                warehouse = formset_form.cleaned_data["warehouse"]
                matching_ordered = ordered_items.filter(part=part)
                # Проверяем, есть ли пришедшие в заказанных,
                # добавляем склад и дату прихода
                batch_update_items = []
                if matching_ordered.exists():
                    match_quantity = len(matching_ordered)
                    if quantity > match_quantity:
                        quantity -= match_quantity
                    else:
                        match_quantity = quantity
                    for item in matching_ordered[:match_quantity]:
                        item.warehouse, item.date = warehouse, date
                        batch_update_items.append(item)
                # Если в приходе больше, чем заказанных,
                # создаём записи для остальных
                if quantity:
                    batch_create_items = [
                        Item(part=part, warehouse=warehouse, date=date)
                        for _ in range(quantity)
                    ]
                    Item.objects.bulk_create(batch_create_items)
                # Берём только что созданные записи для добавления в историю
                created_items = list(
                    Item.objects.filter(
                        date=date, part=part, logs=None, order=None
                    )
                )
                log_items = created_items + batch_update_items
                log.items.set(log_items)
                log.save()
            Item.objects.bulk_update(batch_update_items, ["warehouse", "date"])

            return redirect("inventory:logs")

        context = {
            "form": form,
            "formset": formset,
            "adding": True,
        }

        return render(request, "inventory/add_items.html", context)


class TakeItemsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View-класс взятия комплектующих протезистом.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user)
        context = {"form": form, "taking": True}
        return render(request, "inventory/take_return_items.html", context)

    def post(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user, request.POST)
        formset = ItemTakeFormSet(data=request.POST, prefix="item")
        if form.is_valid():
            job = form.cleaned_data["job"]
            # queryset для выбора комплектующих
            form_kwargs = {"queryset": self.get_queryset(job)}
            # проверяем наличие форм в формсете,
            # что будет означать, что клиент в форме не изменился
            if formset.forms:
                formset = ItemTakeFormSet(
                    request.POST, form_kwargs=form_kwargs, prefix="item"
                )
                if formset.is_valid():
                    comment = form.cleaned_data["comment"]
                    operation = InventoryLog.Operation.TAKE
                    batch_items = []
                    # записываем комплектующие, чтобы избавиться от повторов
                    parts = []
                    items_filter = Q(job=None) & (
                        Q(reserved=job) | Q(reserved=None)
                    )
                    for formset_form in formset:
                        quantity = formset_form.cleaned_data["quantity"]
                        # Если кол-во не указано или <= 0, то пропустить
                        if quantity is None or quantity <= 0:
                            continue
                        part = formset_form.cleaned_data["part"]
                        # Если модель комплектующего повторилась, то пропустить
                        if part in parts:
                            continue
                        parts.append(part)
                        # фильтруем: в первую очередь самые старые со склада 2
                        items = Item.objects.filter(
                            items_filter & Q(part=part)
                        ).order_by("-warehouse", "date")[:quantity]
                        log = InventoryLog(
                            operation=operation,
                            job=job,
                            prosthetist=request.user,
                            comment=comment,
                        )
                        # сохраняем операцию, чтобы создать
                        # Many-to-Many связь с комплектующими
                        log.save()
                        log = InventoryLog.objects.get(id=log.id)
                        log.items.set(items)
                        log.save()
                        batch_items += list(items)
                    for item in batch_items:
                        item.job = job
                    if batch_items:
                        Item.objects.bulk_update(batch_items, ["job"])
                    return redirect("inventory:nomenclature")
            # если клиент в форме изменился, меняем queryset в формсете
            else:
                formset = ItemTakeFormSet(
                    form_kwargs=form_kwargs, prefix="item"
                )

        context = {"form": form, "taking": True, "formset": formset}
        return render(request, "inventory/take_return_items.html", context)

    def get_queryset(self, job):
        qs_filter = Q(items__job=None) & (
            Q(items__reserved=job) | Q(items__reserved=None)
        )
        queryset = Part.objects.annotate(
            available=Count("items", filter=qs_filter),
        ).order_by("vendor_code")
        return queryset


class ReturnItemsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View-class возврата комплектующих на склад.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user)
        formset = ItemReturnFormSet()
        context = {"form": form, "taking": False, "formset": formset}
        return render(request, "inventory/take_return_items.html", context)

    def post(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user, request.POST)
        formset = ItemReturnFormSet(request.POST, prefix="item")
        if form.is_valid():
            job = form.cleaned_data["job"]
            if not formset.forms:
                queryset = self.get_queryset(job)
                formset = ItemReturnFormSet(
                    None, initial=queryset, prefix="item"
                )
                for i, formset_form in enumerate(formset):
                    part = queryset[i]
                    max_parts = part["max_parts"]
                    units = Part.objects.get(
                        id=part["part_id"]
                    ).get_units_display()
                    formset_form.fields["quantity"].widget.attrs.update(
                        {
                            "max": max_parts,
                            "placeholder": f"не больше {max_parts} {units}",
                        }
                    )
            elif formset.is_valid():
                # возвращаем в приоритете самые новые со склада 1
                job_items = job.items.order_by("warehouse", "-date", "-id")
                comment = form.cleaned_data["comment"]
                operation = InventoryLog.Operation.RETURN
                # сюда записываем какие модели комплектующих были возвращены
                parts = []
                batch_logs = []
                # партия возвращаемых на массовое обновление
                batch_items = []
                # партия резервов на массовое обновление
                batch_reserved = []
                for formset_form in formset:
                    quantity = formset_form.cleaned_data["quantity"]
                    # Если кол-во не указано или <= 0, то пропустить
                    if quantity is None or quantity <= 0:
                        continue
                    part_id = formset_form.cleaned_data["part_id"]
                    part = get_object_or_404(Part, id=part_id)
                    parts.append((part, quantity))
                    # срезаем кол-во которое нужно вернуть
                    items = job_items.filter(part=part)[:quantity]
                    log = InventoryLog(
                        operation=operation,
                        job=job,
                        prosthetist=request.user,
                        comment=comment,
                    )
                    log.save()
                    log = InventoryLog.objects.get(id=log.id)
                    log.items.set(items)
                    log.save()
                    batch_items += list(items)
                    batch_logs.append(log)

                for item in batch_items:
                    item.job = None
                    item.reserved = None
                # сохраняем обновления
                if batch_items:
                    Item.objects.bulk_update(batch_items, ["job", "reserved"])
                if batch_reserved:
                    Item.objects.bulk_update(batch_reserved, ["reserved"])
                # пересчитываем резервы для возвращённых моделей комплектующих
                for part, quantity in parts:
                    recalc_reserves(part, quantity)

                return redirect("inventory:logs")

        context = {"form": form, "taking": False, "formset": formset}
        return render(request, "inventory/take_return_items.html", context)

    def get_queryset(self, job):
        queryset = (
            job.items.values("part__vendor_code")
            .annotate(
                max_parts=Count("part__vendor_code"),
                part_name=Concat(
                    F("part__vendor_code"), Value(" "), F("part__name")
                ),
                units=F("part__units"),
            )
            .values("max_parts", "part_id", "part_name", "units")
            .annotate(part=F("part_name"))
        )
        return queryset


class PickPartsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View-class выбора комплектующих протезистом и дозаказ недостающих.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, *args, **kwargs):
        client_form = JobSelectForm(user=request.user)
        context = {"forms": [client_form]}
        return render(request, "inventory/pick_parts.html", context)

    def post(self, request, *args, **kwargs):
        client_form = JobSelectForm(user=request.user, data=request.POST)
        prosthesis_form = ProsthesisSelectForm(data=request.POST or None)
        formset = PickPartsFormSet(data=request.POST)
        if client_form.is_valid():
            job = client_form.cleaned_data["job"]
            queryset = self.get_queryset(job)
            if not formset.forms:
                initial = {"prosthesis": job.prosthesis}
                prosthesis_form = ProsthesisSelectForm(
                    initial=initial, job=job
                )
                formset = PickPartsFormSet(
                    None, initial=queryset.values("part", "quantity")
                )
            elif prosthesis_form.is_valid() and formset.is_valid():
                # записываем модели комплектующих в текущем резерве
                initial_parts = dict(queryset.values_list("id", "quantity"))
                parts = []
                for formset_form in formset:
                    part = formset_form.cleaned_data["part"]
                    if part in parts:
                        continue
                    parts.append(part)
                    quantity = formset_form.cleaned_data["quantity"]
                    if part.id in initial_parts:
                        old_quantity = initial_parts[part.id]
                        # если указанное кол-во больше исходного,
                        # то выделяем резерв
                        if quantity > old_quantity:
                            create_reserve(part, job, quantity - old_quantity)
                        # если меньше, возвращаем и пересчитываем резервы
                        elif quantity < old_quantity:
                            # кол-во комплектующих, которые нужно пересчитать
                            recalc_n = remove_reserve(
                                part, job, old_quantity - quantity
                            )
                            recalc_reserves(part, recalc_n)
                    elif quantity:
                        create_reserve(part, job, quantity)

                prosthesis = prosthesis_form.cleaned_data["prosthesis"]
                job.prosthesis = prosthesis
                job.save()

                return redirect("inventory:logs")

        context = {
            "forms": [client_form, prosthesis_form],
            "formset": formset,
        }
        return render(request, "inventory/pick_parts.html", context)

    def get_queryset(self, job):
        queryset = (
            Part.objects.filter(items__reserved=job)
            .annotate(
                quantity=Count("items", filter=Q(items__reserved=job)),
                part=F("pk"),
            )
            .order_by("vendor_code")
        )
        return queryset


class FreeOrderItemsView(LoginRequiredMixin, View):
    """
    View-класс свободного заказа.
    """

    def get(self, request, *args, **kwargs):
        formset = FreeOrderFormSet()
        context = {"formset": formset}
        return render(request, "inventory/free_order.html", context)

    def post(self, request, *args, **kwargs):
        formset = FreeOrderFormSet(request.POST)
        if formset.forms and formset.is_valid():
            order = get_object_or_404(Order, current=True)
            batch_items = []
            for formset_form in formset:
                quantity = formset_form.cleaned_data["quantity"]
                # Если кол-во не указано или <= 0, то пропустить
                if quantity is None or quantity <= 0:
                    continue
                part = formset_form.cleaned_data["part"]
                batch_items += [
                    Item(part=part, order=order) for _ in range(quantity)
                ]
            Item.objects.bulk_create(batch_items)
            return redirect("inventory:order")

        context = {"formset": formset}
        return render(request, "inventory/free_order.html", context)


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
            order.date = timezone.now()
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


class InventoryLogsListView(tables.SingleTableView):
    """
    View-класс логов инвентаря.
    """

    table_class = InventoryLogsTable
    paginator_class = LazyPaginator
    paginate_by = 30

    def get_queryset(self) -> QuerySet[Any]:
        queryset = InventoryLog.objects.annotate(
            item_count=Count("items"),
            vendor_code=F("items__part__vendor_code"),
            part_name=F("items__part__name"),
        ).order_by("-date")
        return queryset


class InventoryLogsDetailView(tables.SingleTableView):
    table_class = InventoryLogItemsTable
    paginator_class = LazyPaginator
    paginate_by = 30

    def get_log(self):
        log = get_object_or_404(InventoryLog, pk=self.kwargs["pk"])
        return log

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.get_log().items.order_by("-id")
        return queryset
