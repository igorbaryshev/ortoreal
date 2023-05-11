import io
import zipfile
from decimal import Decimal
from functools import wraps

from django.contrib.auth import get_user_model
from django.db.models import Case, F, Q, When
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.utils import timezone

from inventory.models import Item, Order

User = get_user_model()


def dec2pre(value):
    """
    Отображение десятичных дробей с двумя знаками после запятой.
    """
    if not value:
        value = 0
    return Decimal(value).quantize(Decimal(".01"))


def get_dec_display(value):
    """
    Отображение десятичных дробей с пробелами между тысячами и запятой в дроби.
    """
    value = dec2pre(value)
    whole, fraction, *_ = str(value).split(".")
    number = [fraction, ","]
    i = len(whole) - 3
    while i > 0:
        number.append(whole[i : i + 3])
        number.append(" ")
        i -= 3
    else:
        number.append(whole[0 : 3 + i])
    result = "".join(map(str, reversed(number)))
    return result


def generate_zip(files):
    """
    Генератор .zip файла.
    """
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(
        mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as zf:
        for f in files:
            zf.writestr(f[0], f[1])

    return mem_zip.getvalue()


def is_prosthetist(f):
    """
    Декоратор проверяющий протезиста.
    """

    @wraps(f)
    def wrapper(request, *args, **kwargs):
        prosthetists = get_list_or_404(User, is_prosthetist=True)
        if request.user in prosthetists:
            return f(request, *args, **kwargs)
        return redirect("inventory:parts")

    return wrapper


def recalc_reserves(part, quantity=None):
    """
    Пересчитать резервы для модели комплектующей.
    """
    # незарезервированные в текущем заказе
    current_unreserved = Item.objects.filter(
        part=part, order__current=True, reserved=None
    ).order_by("-id")
    # в начале самый ранний резерв, который ещё не заказан
    reserved_items = (
        Item.objects.filter(job=None, reserved__isnull=False, part=part)
        .annotate(
            # если комплектующая добавлена приходом, но не была в заказе,
            # то она неправильно отсортируется вместе заказанными,
            # поэтому сами делаем её заказ не текущим для сортировки
            is_current=Case(
                When(order__isnull=False, then=("order__current")),
                default=False,
            )
        )
        .order_by("is_current", "warehouse", "reserved__date", "date")
    )
    # в начале самая ранняя неиспользуемая комплектующая со склада 2
    unused_items = Item.objects.filter(
        job=None, reserved=None, warehouse__isnull=False, part=part
    ).order_by("-warehouse", "date")
    if quantity is not None:
        unused_items = unused_items[:quantity]
    batch_update = []
    i = 0
    j = 0
    k = 0
    # проходим по срезу неиспользованных комплектующих
    while i < len(reserved_items) and j < len(unused_items):
        reserve = reserved_items[i]
        unused = unused_items[j]
        # если резерв ещё не появлялся на складе
        if reserve.warehouse is None:
            unused.reserved = reserve.reserved
            batch_update.append(unused)
            # если заказ резерва ещё не сделан, то
            # удаляем его, и он удалится из текущего заказа
            if reserve.order.current:
                reserve.delete()
            # если сделан, то убираем резерв
            else:
                reserve.reserved = None
                batch_update.append(reserve)
            j += 1
        # если склад неиспользованного > склада резерва
        # или склад одинаковый, но дата раньше даты зарезервированного
        elif (
            unused.warehouse > reserve.warehouse
            or unused.warehouse == reserve.warehouse
            and unused.date < reserve.date
        ):
            unused.reserved = reserve.reserved
            reserve.reserved = None
            # удаляем из заказа, т.к. резерв освободился
            if k < len(current_unreserved):
                current_unreserved[k].delete()
                k += 1
            batch_update.append(unused)
            batch_update.append(reserve)
            j += 1
        i += 1
    if batch_update:
        Item.objects.bulk_update(batch_update, ["reserved"])


def create_reserve(part, job, quantity):
    """
    Зарезервировать комплектующие.
    """
    unused_items = (
        Item.objects.filter(job=None, reserved=None, part=part)
        .annotate(
            warehouse_old_new=Case(
                When(warehouse__isnull=False, then=1),
                When(order__current=False, then=2),
                default=3,
            )
        )
        .order_by("warehouse_old_new", "-warehouse", "date")
    )
    batch = []
    if quantity <= unused_items.count():
        unused_items = unused_items[:quantity]
        quantity = 0
    else:
        quantity -= unused_items.count()

    for item in unused_items:
        item.reserved = job
        batch.append(item)

    if batch:
        Item.objects.bulk_update(batch, ["reserved"])

    # дозаказываем недостающее на складе и в старых заказах
    if quantity:
        order = Order.objects.get(current=True)
        new_items = [Item(reserved=job, order=order) for _ in range(quantity)]
        Item.objects.bulk_create(new_items)

    # возвращаем кол-во добавленных в новый заказ
    return quantity


def remove_reserve(part, job, quantity):
    reserved_items = (
        Item.objects.filter(job=None, reserved=job, part=part)
        .annotate(
            new_old_warehouse=Case(
                When(order__current=True, then=1),
                When(order__current=False, then=2),
                default=3,
            )
        )
        .order_by("new_old_warehouse", "warehouse", "-date")
    )
    if quantity <= reserved_items.count():
        reserved_items = reserved_items[:quantity]
    else:
        quantity = reserved_items.count()

    batch = []
    for item in reserved_items:
        if item.order.current == True:
            item.delete()
        else:
            item.reserved = None
            batch.append(item)

    if batch:
        Item.objects.bulk_update(batch, ["reserved"])

    # возвращаем кол-во освобожденных резервов
    return quantity
