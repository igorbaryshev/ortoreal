import io
import urllib
from collections import OrderedDict, defaultdict
from decimal import Decimal
from typing import Any, Dict, Optional

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    Case,
    Count,
    F,
    Max,
    Q,
    QuerySet,
    Sum,
    Value,
    When,
    Window,
)
from django.db.models.functions import Concat, RowNumber
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic.list import ListView

import django_tables2 as tables
from django_filters.views import FilterView
from django_tables2.export.views import ExportMixin
from django_tables2.paginators import LazyPaginator
from xlsxwriter.workbook import Workbook

from clients.models import Client, Job
from inventory.filters import MarginFilter, PartFilter
from inventory.forms import (
    CommentForm,
    FreeOrderFormSet,
    InventoryAddForm,
    InventoryTakeForm,
    ItemReturnFormSet,
    ItemTakeFormSet,
    JobSelectForm,
    PartAddFormSet,
    PickPartsFormSet,
    ProsthesisSelectForm,
    ReceptionItemFormSet,
)
from inventory.models import (
    InventoryLog,
    Item,
    Order,
    Part,
    Prosthesis,
    Vendor,
)
from inventory.tables import (
    InventoryLogItemsTable,
    InventoryLogsTable,
    JobSetsTable,
    MarginTable,
    NomenclatureTable,
    OrdersTable,
    OrderTable,
    PartItemsTable,
    VendorExportTable,
    VendorOrderTable,
)
from inventory.utils import (
    OrderedCounter,
    check_minimum_remainder,
    create_reserve,
    generate_zip,
    move_reserves_to_free_order,
    remove_excess_from_current_order,
    remove_reserve,
    reorg_reserves,
)

PARTS_PER_PAGE = 20


class LoginRequiredMixin(LoginRequiredMixin):
    login_url = "/admin/login/"
    redirect_field_name = "next"


class NomenclatureListView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    tables.SingleTableMixin,
    FilterView,
):
    """
    View номенклатуры.
    """

    table_class = NomenclatureTable
    model = Part
    paginate_by = PARTS_PER_PAGE
    template_name = "inventory/nomenclature.html"

    filterset_class = PartFilter

    def test_func(self) -> bool:
        return self.request.user.is_manager or self.request.user.is_staff

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Part.objects.order_by("vendor_code")
        return queryset


class PartItemsListView(
    LoginRequiredMixin, UserPassesTestMixin, tables.SingleTableView
):
    """
    View списка комплектующих данной модели на складе.
    """

    table_class = PartItemsTable
    paginate_by = PARTS_PER_PAGE

    def test_func(self) -> bool:
        return self.request.user.is_manager

    def get_part(self):
        pk = self.kwargs.get("pk")
        part = get_object_or_404(Part, pk=pk)
        return part

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Item.objects.filter(
            part=self.get_part(), job=None, arrived=True
        ).order_by("-date")
        return queryset


class ReceptionView(LoginRequiredMixin, View):
    """
    Приход.
    """

    def get(self, request, *args, **kwargs):
        form = InventoryAddForm()
        formset = ReceptionItemFormSet()
        context = {
            "form": form,
            "formset": formset,
        }
        return render(request, "inventory/reception.html", context)

    def post(self, request, *args, **kwargs):
        form = InventoryAddForm(request.POST)
        formset = ReceptionItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid() and formset.forms:
            date = form.cleaned_data["date"]
            operation = InventoryLog.Operation.RECEPTION
            comment = form.cleaned_data["comment"]
            # фильтр: не назначен склад, не в текущем заказе,
            # сортировка по дате резерва, без резерва - в последнюю очередь
            ordered_items = Item.objects.filter(
                arrived=False, order__current=False
            ).order_by(F("reserved__date").asc(nulls_last=True), F("id").asc())
            for fs_form in formset:
                print(fs_form.cleaned_data["quantity"])
                quantity = fs_form.cleaned_data["quantity"]
                # Если кол-во не указано или <= 0, то пропустить
                if quantity is None or quantity <= 0:
                    continue
                log = InventoryLog(
                    operation=operation,
                    comment=comment,
                )
                log.save()
                log = InventoryLog.objects.get(id=log.id)
                part = fs_form.cleaned_data["part"]
                price = fs_form.cleaned_data["price"]
                vendor2 = fs_form.cleaned_data["vendor2"]
                matching_ordered = ordered_items.filter(part=part)
                # Проверяем, есть ли пришедшие в заказанных,
                # добавляем склад и заменяем дату на дату прихода
                batch_update_items = []
                if matching_ordered.exists():
                    match_quantity = len(matching_ordered)
                    if quantity > match_quantity:
                        quantity -= match_quantity
                    else:
                        match_quantity = quantity
                        # обнуляем кол-во, чтобы не создавать новые записи
                        quantity = 0
                    for item in matching_ordered[:match_quantity]:
                        item.date = date
                        item.arrived = True
                        item.vendor2 = vendor2
                        batch_update_items.append(item)
                # Если в приходе больше, чем заказанных,
                # создаём записи для остальных
                if quantity:
                    batch_create_items = [
                        Item(
                            part=part,
                            arrived=True,
                            vendor2=vendor2,
                            price=price,
                            date=date,
                        )
                    ] * quantity
                    Item.objects.bulk_create(batch_create_items)
                # Берём только что созданные записи для добавления в историю
                created_items = list(
                    Item.objects.filter(
                        date=date,
                        part=part,
                        logs=None,
                        order=None,
                        arrived=True,
                    )
                )
                # Объединяем созданные и обновляемые записи для лога
                log_items = created_items + batch_update_items
                log.items.set(log_items)
                log.save()
            Item.objects.bulk_update(
                batch_update_items, ["date", "arrived", "price"]
            )

            return redirect("inventory:logs")

        context = {
            "form": form,
            "formset": formset,
        }

        return render(request, "inventory/reception.html", context)


class TakeItemsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View расхода комплектующих протезистом.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist or self.request.user.is_manager

    def get(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user)
        context = {"form": form, "taking": True}
        return render(request, "inventory/take_return_items.html", context)

    def post(self, request, *args, **kwargs):
        form = InventoryTakeForm(request.user, request.POST)
        formset = ItemTakeFormSet(request.POST)
        if form.is_valid():
            job = form.cleaned_data["job"]
            # queryset для выбора комплектующих
            form_kwargs = {"queryset": self.get_queryset(job)}
            # проверяем наличие форм в формсете,
            # что будет означать, что клиент в форме не изменился
            if formset.forms:
                formset = ItemTakeFormSet(
                    request.POST, form_kwargs=form_kwargs
                )
                if formset.is_valid():
                    comment = form.cleaned_data["comment"]
                    operation = InventoryLog.Operation.TAKE
                    batch_items = []
                    # записываем комплектующие, чтобы избавиться от повторов
                    parts = []
                    items_filter = (
                        Q(arrived=True)
                        & Q(job=None)
                        & (
                            Q(reserved=job)
                            | Q(reserved=None)
                            | Q(reserved__date__gt=job.date)
                        )
                    )
                    for fs_form in formset:
                        quantity = fs_form.cleaned_data["quantity"]
                        # Если кол-во не указано или <= 0, то пропустить
                        if quantity is None or quantity <= 0:
                            continue
                        part = fs_form.cleaned_data["part"]
                        # Если модель комплектующего повторилась, то пропустить
                        if part in parts:
                            continue
                        parts.append(part)
                        # фильтруем: в первую очередь самые старые со склада 2
                        items = Item.objects.filter(
                            items_filter & Q(part=part)
                        ).order_by("-vendor2", "date")[:quantity]
                        log = InventoryLog(
                            operation=operation,
                            job=job,
                            prosthetist=job.prosthetist,
                            comment=comment,
                        )
                        # сохраняем операцию, чтобы создать
                        # Many-to-Many связь с комплектующими
                        log.save()
                        log = InventoryLog.objects.get(id=log.id)
                        log.items.set(items)
                        log.save()
                        batch_items += list(items)
                    # упорядоченный словарь моделей комплектующих, в которых
                    # хранятся работы с кол-вом комплектующих
                    # для нового резерва
                    parts_to_reserve = defaultdict(OrderedCounter)
                    for item in batch_items:
                        # если комплектующая была взята из чужого резерва,
                        # то записываем взятый резерв
                        if item.reserved != job:
                            # берём словарь модели комплектующей, увеличиваем
                            # кол-во требуемое в резерв работе, у которой взяли
                            parts_to_reserve[item.part][item.reserved] += 1
                            item.reserved = job
                        item.job = job

                    if batch_items:
                        Item.objects.bulk_update(
                            batch_items, ["job", "reserved"]
                        )

                    # пересоздаём резервы для всех, у кого взяли
                    if parts_to_reserve:
                        for part, job_dict in parts_to_reserve.items():
                            print(job_dict)
                            # берём первую работу и кол-во из словаря
                            job, quantity = job_dict.popitem(last=False)
                            create_reserve(
                                part, job, quantity, job_dict=job_dict
                            )
                    # проверяем неснижаемый остаток
                    check_minimum_remainder()

                    return redirect("inventory:nomenclature")
            # если клиент в форме изменился, меняем queryset в формсете
            else:
                formset = ItemTakeFormSet(form_kwargs=form_kwargs)

        context = {"form": form, "taking": True, "formset": formset}
        return render(request, "inventory/take_return_items.html", context)

    def get_queryset(self, job):
        # разрешить брать из чужих резервов, если они новее
        qs_filter = (
            Q(items__arrived=True)
            & Q(items__job=None)
            & (
                Q(items__reserved=job)
                | Q(items__reserved=None)
                | Q(items__reserved__date__gt=job.date)
            )
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
        return self.request.user.is_prosthetist or self.request.user.is_manager

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
                for i, fs_form in enumerate(formset):
                    part = queryset[i]
                    max_parts = part["max_parts"]
                    units = Part.objects.get(id=part["part_id"]).units or ""
                    fs_form.fields["quantity"].widget.attrs.update(
                        {
                            "max": max_parts,
                            "placeholder": f"не больше {max_parts} {units}",
                        }
                    )
            elif formset.is_valid():
                # возвращаем в приоритете самые новые не от поставщика 2
                job_items = job.items.order_by("vendor2", "-date", "-id")
                comment = form.cleaned_data["comment"]
                operation = InventoryLog.Operation.RETURN
                # сюда записываем какие модели комплектующих были возвращены
                parts = []
                batch_logs = []
                # партия возвращаемых на массовое обновление
                batch_items = []
                # партия резервов на массовое обновление
                batch_reserved = []
                for fs_form in formset:
                    quantity = fs_form.cleaned_data["quantity"]
                    # Если кол-во не указано или <= 0, то пропустить
                    if quantity is None or quantity <= 0:
                        continue
                    part_id = fs_form.cleaned_data["part_id"]
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
                    reorg_reserves(part)

                # удаляем возможные излишки из текущего заказа после пересчёта
                remove_excess_from_current_order()

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
    View выбора комплектующих протезистом, и дозаказ недостающих.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, *args, **kwargs):
        client_form = JobSelectForm(user=request.user)
        context = {"forms": [client_form]}
        return render(request, "inventory/pick_parts.html", context)

    def post(self, request, *args, **kwargs):
        client_form = JobSelectForm(user=request.user, data=request.POST)
        job_pk = kwargs.get("job", None)
        if job_pk is not None:
            job = get_object_or_404(Job, pk=job_pk)
            client_form = JobSelectForm(
                user=request.user, initial={"job": job}
            )
        prosthesis_form = ProsthesisSelectForm(data=request.POST or None)
        formset = PickPartsFormSet(data=request.POST)
        if client_form.is_valid():
            job = client_form.cleaned_data["job"]
            queryset = self.get_queryset(job)
            # если формсет пустой, то задаём исходные данные
            if not formset.forms:
                initial = {"prosthesis": job.prosthesis}
                prosthesis_form = ProsthesisSelectForm(
                    initial=initial, job=job
                )
                formset = PickPartsFormSet(
                    initial=queryset.values("part", "quantity")
                )
            # иначе, проверяем валидность формы протеза и формсета
            elif prosthesis_form.is_valid() and formset.is_valid():
                # записываем модели комплектующих в текущем резерве
                initial_parts = dict(queryset.values_list("id", "quantity"))
                parts = []
                for fs_form in formset:
                    part = fs_form.cleaned_data["part"]
                    if part.id in parts:
                        continue
                    parts.append(part.id)
                    quantity = fs_form.cleaned_data["quantity"]
                    if part.id in initial_parts:
                        old_quantity = initial_parts[part.id]
                        # если указанное кол-во больше исходного,
                        # то выделяем резерв
                        if quantity > old_quantity:
                            create_reserve(part, job, quantity - old_quantity)
                        # если меньше, возвращаем и пересчитываем резервы
                        elif quantity < old_quantity:
                            # удалить резервы
                            remove_reserve(part, job, old_quantity - quantity)
                            # пересчитать резервы,
                            reorg_reserves(part, job)
                    elif quantity:
                        create_reserve(part, job, quantity)
                # проверяем удалённые строки
                for part_id, quantity in initial_parts.items():
                    if part_id not in parts:
                        part = Part.objects.get(id=part_id)
                        remove_reserve(part, job, quantity)
                        reorg_reserves(part, job)

                prosthesis = prosthesis_form.cleaned_data["prosthesis"]
                job.prosthesis = prosthesis
                job.save()
                check_minimum_remainder()

                return redirect("inventory:job_sets")

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


class FreeOrderAddView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View свободного заказа.
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff or self.request.user.is_manager

    def get(self, request, *args, **kwargs):
        formset = FreeOrderFormSet()
        context = {"formset": formset}
        return render(request, "inventory/free_order.html", context)

    def post(self, request, *args, **kwargs):
        formset = FreeOrderFormSet(request.POST)
        if formset.forms and formset.is_valid():
            order = get_object_or_404(Order, current=True)
            batch_create = []
            for fs_form in formset:
                quantity = fs_form.cleaned_data["quantity"]
                # Если кол-во не указано или <= 0, то пропустить
                if quantity is None or quantity <= 0:
                    continue
                part = fs_form.cleaned_data["part"]
                print(part)
                price = part.items.aggregate(Max("price")).get(
                    "price__max", Decimal("0.00")
                )
                if price is None:
                    price = Decimal("0.00")
                print(price)
                batch_create += [
                    Item(part=part, order=order, free_order=True, price=price)
                ] * quantity

            Item.objects.bulk_create(batch_create)

            print(move_reserves_to_free_order())
            print(remove_excess_from_current_order())

            return redirect("inventory:order")

        context = {"formset": formset}
        return render(request, "inventory/free_order.html", context)


class FreeOrderEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View изменения свободного заказа.
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff or self.request.user.is_manager

    def get(self, request, *args, **kwargs):
        formset = FreeOrderFormSet(initial=self.get_initial())
        context = {"formset": formset, "editing": True}
        return render(request, "inventory/free_order.html", context)

    def post(self, request, *args, **kwargs):
        formset = FreeOrderFormSet(request.POST)
        if formset.is_valid():
            initial = dict(
                Part.objects.annotate(
                    quantity=Count(
                        "items",
                        filter=Q(items__order__current=True)
                        & Q(items__free_order=True),
                    )
                )
                .exclude(quantity=0)
                .values_list("id", "quantity")
            )
            # записываем модели комплектующих, которые были проверены
            parts = []
            batch_create = []
            batch_update = []
            order = get_object_or_404(Order, current=True)
            for form in formset:
                part = form.cleaned_data["part"]
                if part.id in parts:
                    continue
                parts.append(part.id)
                quantity = form.cleaned_data["quantity"]
                # Если модель указана в исходных данных, то изменяем их
                if part.id in initial:
                    initial_quantity = initial[part.id]
                    if quantity > initial_quantity:
                        batch_create += self.create_items(
                            part.id, quantity - initial_quantity, order
                        )
                    elif quantity < initial_quantity:
                        # если кол-во уменьшено, то убрать незарезервированные,
                        # а зарезервированным изменить заказ на обычный,
                        # незарезервированные в начале списка
                        batch_update += self.remove_from_order(
                            part.id, initial_quantity - quantity
                        )
                # Если нет, то просто создаём записи комплектующих
                else:
                    batch_create += self.create_items(part.id, quantity, order)
            # Проходим по исходным, ищем удалённые
            for part_id, quantity in initial.items():
                # Если модель была удалена из заказа, то удаляем записи
                if part_id not in parts:
                    batch_update += self.remove_from_order(part_id, quantity)

            # обновляем комплектующие, которые больше не в свободном заказе
            if batch_update:
                Item.objects.bulk_update(batch_update, ["free_order"])

            # создаём записи комплектующих и перемещаем на них обычные заказы
            if batch_create:
                Item.objects.bulk_create(batch_create)
                move_reserves_to_free_order()

            check_minimum_remainder()
            return redirect("inventory:order")

        context = {"formset": formset, "editing": True}
        return render(request, "inventory/free_order.html", context)

    def remove_from_order(self, part_id, quantity=None):
        """
        Метод снимает свободный заказ с зарезервированного и
        удаляет незарезервированное.
        Возвращает список для обновления.
        """
        batch_update = []
        items = Item.objects.filter(
            part_id=part_id, order__current=True, free_order=True
        ).order_by("reserved")
        if quantity is not None:
            items = items[:quantity]
        batch_update = []
        for item in items:
            # если было в резерве, то делаем обычным заказом
            if item.reserved:
                item.free_order = False
                batch_update.append(item)
            # иначе, удаляем из заказа
            else:
                item.delete()

        return batch_update

    def create_items(self, part_id, quantity, order):
        """
        Возвращает список для создания.
        """
        items = [
            Item(part_id=part_id, order=order, free_order=True)
        ] * quantity
        return items

    def get_initial(self):
        initial = (
            Item.objects.filter(order__current=True, free_order=True)
            .values("part")
            .annotate(quantity=Count("part"))
            .order_by("part__vendor_code")
        )
        return initial


class AddPartsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View добавления моделей комплектующих.
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff or self.request.user.is_manager

    def get(self, request):
        formset = PartAddFormSet(prefix="item")

        context = {
            "formset": formset,
        }
        return render(request, "inventory/add_items.html", context)

    def post(self, request):
        formset = PartAddFormSet(request.POST or None, prefix="item")
        if formset.is_valid():
            for form in formset:
                if form.is_valid():
                    form.save()

            return redirect("inventory:nomenclature")

        context = {
            "formset": formset,
        }
        return render(request, "inventory/add_items.html", context)


class OrderView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    ExportMixin,
    tables.SingleTableView,
):
    """
    View заказа.
    """

    table_class = OrderTable
    template_name = "inventory/order.html"

    def test_func(self) -> bool:
        if self.request.user.is_staff or self.request.user.is_manager:
            return True
        return False

    @property
    def is_current(self):
        if self.kwargs.get("pk"):
            return False
        return True

    def get_order(self):
        if self.is_current:
            return get_object_or_404(Order, current=True)
        return get_object_or_404(Order, pk=self.kwargs.get("pk"))

    def get(self, request, pk=None):
        check_minimum_remainder()
        return super().get(request)

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
                price=Max("price"),
                quantity=Count("part"),
                vendor=F("part__vendor__name"),
                price_mul=F("quantity") * F("price"),
            )
            .order_by("vendor_code")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current"] = self.is_current
        order = self.get_order()
        context["title"] = "Заказ от"
        if order.current:
            context["title"] = "Текущий заказ c"
        context["date"] = order.date
        return context


class OrdersView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    ExportMixin,
    tables.SingleTableView,
):
    """
    View списка всех заказов.
    """

    table_class = OrdersTable
    paginator_class = LazyPaginator
    paginate_by = PARTS_PER_PAGE

    def test_func(self) -> bool:
        if self.request.user.is_staff or self.request.user.is_manager:
            return True
        return False

    def get_queryset(self) -> QuerySet[Any]:
        return Order.objects.order_by("-id")


def export_orders(request):
    """
    Экспорт заказов по поставщикам в .zip архиве.
    """
    queryset = Order.objects.get(current=True)
    vendors = (
        queryset.items.annotate(
            vendor_id=F("part__vendor__id"),
            name=Case(
                When(part__vendor__isnull=True, then=Value("-")),
                default=F("part__vendor__name"),
            ),
        )
        .values("vendor_id", "name")
        .distinct()
    )
    table_queryset = (
        queryset.items.values("part")
        .annotate(
            row=Window(RowNumber()),
            vendor_code=F("part__vendor_code"),
            # price=F("part__price"),
            quantity=Count("part"),
            # price_mul=F("quantity") * F("price"),
        )
        .order_by("vendor_code")
    )
    files = []
    for vendor in vendors:
        vendor_queryset = table_queryset.filter(
            part__vendor_id=vendor["vendor_id"]
        )
        table = VendorExportTable(vendor_queryset)
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
        files.append((vendor["name"] + ".xlsx", table_file))

    current_date = timezone.now().strftime("%Y-%m-%d_%H-%M")
    zip_name = urllib.parse.quote(f"Заказ_от_{current_date}")
    response = HttpResponse(generate_zip(files))
    response["Content-Type"] = "application/x-zip-compressed"
    response[
        "Content-Disposition"
    ] = f"attachment; filename*=UTF-8''{zip_name}.zip"

    return response


class InventoryLogsListView(tables.SingleTableView):
    """
    View логов инвентаря.
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
    table_class = PartItemsTable
    paginator_class = LazyPaginator
    paginate_by = 30

    def get_log(self):
        log = get_object_or_404(InventoryLog, pk=self.kwargs["pk"])
        return log

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.get_log().items.order_by("-id")
        return queryset


class JobSetView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Изменение комплектации по id.
    """

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get(self, request, *args, **kwargs):
        job = get_object_or_404(Job, pk=kwargs.get("pk", None))
        queryset = self.get_queryset(job)
        form = ProsthesisSelectForm(job=job)
        formset = PickPartsFormSet(initial=queryset.values("part", "quantity"))

        context = {"form": form, "formset": formset}
        return render(request, "inventory/job_set.html", context)

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


class JobSetsView(
    LoginRequiredMixin, UserPassesTestMixin, tables.SingleTableView
):
    """
    View комплектов клиентов протезиста.
    """

    table_class = JobSetsTable
    paginator_class = LazyPaginator
    paginate_by = PARTS_PER_PAGE

    def test_func(self) -> bool:
        return self.request.user.is_prosthetist

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Job.objects.filter(prosthetist=self.request.user).order_by(
            "-date"
        )
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = f"{self.request.user}. Клиенты."

        return context


class AllJobSetsView(JobSetsView):
    """
    View комплектов всех клиентов для менеджера.
    """

    def test_func(self) -> bool:
        return self.request.user.is_manager

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Job.objects.order_by("-date")
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(tables.SingleTableView, self).get_context_data(
            **kwargs
        )
        context["title"] = "Все клиенты."

        return context


class MarginView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    tables.SingleTableMixin,
    FilterView,
):
    """
    View таблицы маржи.
    """

    table_class = MarginTable
    paginate_by = PARTS_PER_PAGE
    filterset_class = MarginFilter
    template_name = "inventory/margin_list.html"

    def test_func(self) -> bool | None:
        return self.request.user.is_manager

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Job.objects.annotate(
            price_items=Sum("items__price"),
            price=Case(
                When(prosthesis__price__isnull=True, then=Decimal("0.00")),
                default=F("prosthesis__price"),
            ),
            margin=F("price") - F("price_items") - Decimal("60000.00"),
        )
        for job in queryset:
            print(job.margin)
        return queryset
