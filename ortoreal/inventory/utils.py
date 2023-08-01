import io
import locale
import zipfile
from collections import Counter, OrderedDict
from decimal import Decimal
from functools import wraps

from django.contrib.auth import get_user_model
from django.db.models import Case, Count, F, Value, When
from django.shortcuts import get_list_or_404, redirect
from django.utils import timezone

from inventory.models import Item, Order, Part

User = get_user_model()


class OrderedCounter(Counter, OrderedDict):
    """
    Упорядоченный счётчик.
    """

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, OrderedDict(self))

    def __reduce__(self):
        return self.__class__, (OrderedDict(self),)


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
    if value is None:
        return
    locale.setlocale(locale.LC_MONETARY, "ru_RU.UTF-8")
    result = locale.currency(value, grouping=True)
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


# def recalc_reserves(part, quantity=None):
#     """
#     Пересчитать резервы для модели комплектующей.
#     """
#     # незарезервированные в текущем заказе, которые не добавлены вручную
#     current_unreserved = Item.objects.filter(
#         part=part, order__current=True, reserved=None, free_order=False
#     ).order_by("-free_order")
#     # в начале самый ранний резерв, который ещё не заказан
#     reserved_items = (
#         Item.objects.filter(job=None, reserved__isnull=False, part=part)
#         .annotate(
#             # если комплектующая добавлена приходом, но не была в заказе,
#             # то она неправильно отсортируется вместе заказанными,
#             # поэтому сами делаем её заказ не текущим для сортировки
#             is_current=Case(
#                 When(order__isnull=False, then=("order__current")),
#                 default=False,
#             )
#         )
#         .order_by("is_current", "warehouse", "reserved__date", "date")
#     )
#     # в начале самая ранняя неиспользуемая комплектующая со склада 2
#     unused_items = Item.objects.filter(
#         job=None, reserved=None, warehouse__isnull=False, part=part
#     ).order_by("-warehouse", "date")
#     if quantity is not None:
#         unused_items = unused_items[:quantity]
#     batch_update = []
#     i = 0
#     j = 0
#     k = 0
#     # проходим по срезу неиспользованных комплектующих
#     while i < len(reserved_items) and j < len(unused_items):
#         reserve = reserved_items[i]
#         unused = unused_items[j]
#         # если резерв ещё не появлялся на складе
#         if reserve.warehouse is None:
#             unused.reserved = reserve.reserved
#             batch_update.append(unused)
#             # если заказ резерва ещё не сделан, то
#             # удаляем его, и он удалится из текущего заказа
#             if (
#                 not reserve.free_order
#                 and reserve.order
#                 and reserve.order.current
#             ):
#                 reserve.delete()
#             # если сделан, то убираем резерв
#             else:
#                 reserve.reserved = None
#                 batch_update.append(reserve)
#             j += 1
#         # если склад неиспользованного > склада резерва
#         # или склад одинаковый, но дата раньше даты зарезервированного
#         elif (
#             unused.warehouse > reserve.warehouse
#             or unused.warehouse == reserve.warehouse
#             and unused.date < reserve.date
#         ):
#             unused.reserved = reserve.reserved
#             reserve.reserved = None
#             # удаляем из тек.заказа, т.к. резерв на складе освободился
#             if k < len(current_unreserved):
#                 current_unreserved[k].delete()
#                 k += 1
#             batch_update.append(unused)
#             batch_update.append(reserve)
#             j += 1
#         i += 1
#     if batch_update:
#         Item.objects.bulk_update(batch_update, ["reserved"])


def reorg_reserves(part, job=None):
    # находим все резервы комплектующих, которые ещё не в работе,
    # и сортируем их от самых ранних работ к самым новым
    reserved_items = Item.objects.filter(
        reserved__isnull=False, job=None, part=part
    ).order_by("reserved__date")
    #    # если указана работа, то оставляем пересчитываем только те резервы,
    #    # которые не раньше этой работы.
    #    if job is not None:
    #        reserved_items.filter(reserved__date__gte=job.date)

    # запоминаем резервы в нужной последовательности,
    # т.к. обнулим и назначим заново
    reserved_items_jobs = reserved_items.values_list("reserved", flat=True)
    # обнуляем резервы
    reserved_items.update(reserved=None)
    # 1. Разбираемся с комплектующими, которые уже есть на складе
    available_items = Item.objects.filter(
        job=None, part=part, arrived=True
    ).order_by("-vendor2", "date")
    batch_update = []
    k = 0
    for item in available_items:
        if k >= len(reserved_items_jobs):
            break
        item.reserved = reserved_items_jobs[k]
        batch_update.append(item)
        k += 1
    # если ещё не прошли по всем резервам, то
    if k < len(reserved_items_jobs):
        # 2. Разбираемся с комплектующими в заказах
        order_items = Item.objects.filter(
            job=None, part=part, arrived=False
        ).order_by("order__date")
        for item in order_items:
            if k >= len(reserved_items_jobs):
                break
            item.reserved = reserved_items_jobs[k]
            batch_update.append(item)
            k += 1

    if batch_update:
        Item.objects.bulk_update(batch_update, ["reserved"])


# def create_reserve(part, job, quantity):
#     """
#     Зарезервировать комплектующие.
#     """
#     unused_items = (
#         Item.objects.filter(job=None, reserved=None, part=part)
#         .annotate(
#             warehouse_old_new=Case(
#                 When(warehouse__isnull=False, then=1),
#                 When(order__current=False, then=2),
#                 default=3,
#             )
#         )
#         .order_by("warehouse_old_new", "-warehouse", "date")
#     )
#     batch = []
#     print(*unused_items.values("id", "warehouse", "order"), sep="\n")
#     if quantity <= unused_items.count():
#         unused_items = unused_items[:quantity]
#         quantity = 0
#     else:
#         quantity -= unused_items.count()

#     for item in unused_items:
#         item.reserved = job
#         batch.append(item)

#     if batch:
#         Item.objects.bulk_update(batch, ["reserved"])

#     # дозаказываем недостающее на складе и в старых заказах
#     if quantity:
#         order = Order.objects.get(current=True)
#         new_items = [
#             Item(reserved=job, order=order, part=part) for _ in range(quantity)
#         ]
#         Item.objects.bulk_create(new_items)

#     # возвращаем кол-во добавленных в новый заказ
#     return quantity


def create_reserve(part, job, quantity, job_dict=OrderedCounter()):
    """
    Зарезервировать комплектующие. Новая версия.
    """

    # 1. Сначала разбираемся с остатками на складе.
    unused_in_warehouse = Item.objects.filter(
        job=None, reserved=None, part=part, arrived=True
    ).order_by("-vendor2")
    if unused_in_warehouse.exists():
        # если запрашиваемое кол-во <= кол-ва на складе
        if quantity <= unused_in_warehouse.count():
            # берём срез из того, что на складе
            unused_in_warehouse = unused_in_warehouse[:quantity]
            quantity = 0
        else:
            # берём, что есть, а кол-во уменьшаем для следующего этапа
            quantity -= unused_in_warehouse.count()
        # резервируем получившиеся незанятые
        for item in unused_in_warehouse:
            item.reserved = job
        Item.objects.bulk_update(unused_in_warehouse, ["reserved"])
    # если все нужные резервы созданы, то выходим
    if not quantity:
        return "unused only"

    # 2. Теперь ищем среди самых новых работ, у которых уже на складе,
    #    забираем у них, а в конце возьмём из старых заказов или дозакажем,
    #    но сначала для нашей работы
    newest_reserves = Item.objects.filter(
        job=None,
        part=part,
        reserved__isnull=False,
        reserved__date__gt=job.date,
        arrived=True,
    ).order_by("-reserved__date")
    # список работ, для которых нужно будет дозаказать
    jobs_to_reserve_for = []
    if newest_reserves.exists():
        # если запрашиваемое кол-во <= кол-ва в резервах у других
        if quantity <= newest_reserves.count():
            # то берём срез из других резервов
            newest_reserves = newest_reserves[:quantity]
            quantity = 0
        else:
            # берём, что есть, а кол-во уменьшаем для следующего этапа
            quantity -= newest_reserves.count()
        # проходим по резервам
        for item in newest_reserves:
            # добавляем работы в список
            jobs_to_reserve_for.append(item.reserved)
            # записываем резерв на нашу работу
            item.reserved = job
        Item.objects.bulk_update(newest_reserves, ["reserved"])
    #    # находим незарезервированные во всех заказах, начиная с самого раннего
    #    unreserved_in_orders = Item.objects.filter(
    #        part=part, warehouse__isnull=True, reserved__isnull=True
    #    ).order_by("order__date", "order__current")

    # 3. Если нужно ещё, то проходим по самым ранним заказанным,
    #    но ещё не на складе
    if quantity:
        # в самом раннем заказе ставим в начало комплектующие без резерва,
        # потом самые новые с резервом
        ordered_reserves = (
            Item.objects.filter(job=None, arrived=False, part=part)
            .annotate(
                reserve_date=Case(
                    # если нет резерва, то записываем сегодняшние дату и время
                    When(reserved__isnull=True, then=Value(timezone.now())),
                    default=F("reserved__date"),
                )
            )
            # оставляем только резервы с датой больше, чем у нашей работы
            .filter(reserve_date__gt=job.date)
            .order_by("order__date", "reserve_date")
        )

        if ordered_reserves.exists():
            # если запрашиваемое кол-во <= кол-ва в непришедших заказах
            if quantity <= ordered_reserves.count():
                ordered_reserves = ordered_reserves[:quantity]
                quantity = 0
            else:
                quantity -= ordered_reserves

        # проходим комплектующим в заказах
        for item in ordered_reserves:
            # если у комплектующей есть резерв, то вносим её работу в список
            if item.reserved is not None:
                jobs_to_reserve_for.append(item.reserved)
            # записываем резерв на нашу работу
            item.reserved = job
        Item.objects.bulk_update(ordered_reserves, ["reserved"])
    # сортируем работы, для которых нужно заново зарезервировать комплектующие
    jobs_to_reserve_for.sort(key=lambda x: x.date)
    # 4. Если так получилось, что не хватило и того, что уже в заказах,
    #    то добавляем всё в текущий заказ
    if quantity:
        order = Order.objects.get(current=True)
        # создаём партию из недостающих комплектующих
        batch_create = [Item(part=part, reserved=job, order=order)] * quantity
        # добавляем в неё недостающие комплектующие более новых работ
        for job_reserve in jobs_to_reserve_for:
            batch_create.append(
                Item(part=part, reserved=job_reserve, order=order)
            )
        Item.objects.bulk_create(batch_create)
        return "ordered more"

    # 5. Если хватило в заказах, то нужно разобраться с резервами для работ,
    #    которые помещены в список.
    job_dict.update(OrderedCounter(jobs_to_reserve_for))
    if job_dict:
        next_job, next_quantity = job_dict.popitem(last=False)
        # повторяем для следующей работы
        create_reserve(part, next_job, next_quantity, job_dict)
    else:
        print("all done")


def remove_reserve(part, job, quantity):
    """
    Снять резерв.
    """
    reserved_items = (
        Item.objects.filter(job=None, reserved=job, part=part)
        .annotate(
            new_old_warehouse=Case(
                When(order__current=True, then=1),
                When(order__current=False, then=2),
                default=3,
            )
        )
        .order_by("new_old_warehouse", "vendor2", "-date")
    )
    if quantity <= reserved_items.count():
        reserved_items = reserved_items[:quantity]
    else:
        quantity = reserved_items.count()

    batch = []
    for item in reserved_items:
        # Если не из свободного заказа и в текущем заказе
        if not item.free_order and item.order and item.order.current:
            item.delete()
        else:
            item.reserved = None
            batch.append(item)

    if batch:
        Item.objects.bulk_update(batch, ["reserved"])

    # возвращаем кол-во освобожденных резервов
    return quantity


def check_minimum_remainder():
    """
    Проверить неснижаемый остаток и добавить нехватки в текущий заказ.
    """
    remaining_parts = (
        Part.objects.filter(
            minimum_remainder__isnull=False,
            items__reserved__isnull=True,
            items__job__isnull=True,
        )
        .exclude(minimum_remainder=0)
        .annotate(item_count=Count("items"))
    )

    order = Order.objects.get(current=True)
    batch_create = []
    for part in remaining_parts:
        if part.minimum_remainder > part.item_count:
            quantity = part.minimum_remainder - part.item_count
            batch_create += [Item(part=part, order=order)] * quantity

    if batch_create:
        Item.objects.bulk_create(batch_create)

    return len(batch_create)


def move_reserves_to_free_order():
    """
    Переместить резервы из обычных заказов в свободный, если есть незанятые.
    """
    current_order = Order.objects.get(current=True)
    unreserved_free_order = current_order.items.filter(
        reserved__isnull=True, free_order=True
    )
    reserved_regular_order = current_order.items.filter(
        reserved__isnull=False, free_order=False
    )
    parts_free_order = Part.objects.filter(
        items__free_order=True,
        items__order__current=True,
        items__reserved__isnull=True,
    ).annotate(item_count=Count("items"))
    parts_regular_order = Part.objects.filter(
        items__free_order=False,
        items__order__current=True,
        items__reserved__isnull=False,
    ).annotate(item_count=Count("items"))
    batch_update = []
    for part in parts_regular_order:
        if part in parts_free_order:
            quantity = part.item_count
            free_order_items = unreserved_free_order.filter(part=part)
            regular_order_items = reserved_regular_order.filter(part=part)
            # берём срез до кол-ва комплектующих в обычном резерве
            free_order_items = free_order_items[:quantity]
            # если в свободном оказалось меньше, то кол-во можно переписать
            quantity = free_order_items.count()
            for i, item in enumerate(regular_order_items[:quantity]):
                # переписываем резерв на свободный заказ и удаляем из обычного
                free_order_items[i].reserved = item.reserved
                batch_update.append(free_order_items[i])
                item.delete()

    if batch_update:
        Item.objects.bulk_update(batch_update, ["reserved"])

    return len(batch_update)


def remove_excess_from_current_order():
    """
    Удалить излишки из текущего заказа.
    """
    # незарезервированные в текущем заказе, заказанные обычным способом
    unreserved_current = Item.objects.filter(
        reserved__isnull=True,
        order__current=True,
        arrived=False,
        free_order=False,
    )
    # всего в остатке
    parts_remainder = Part.objects.filter(
        items__reserved__isnull=True, items__job__isnull=True
    ).annotate(item_count=Count("items"))
    parts_unreserved_current = Part.objects.filter(
        items__reserved__isnull=True,
        items__order__current=True,
        items__free_order=False,
    )
    batch_delete = []
    for part in parts_remainder:
        if part in parts_unreserved_current:
            quantity = part.item_count
            # если у комплектующей есть неснижаемый остаток,
            # то меняем кол-во удаляемых
            min_remainder = part.minimum_remainder
            if (
                min_remainder is not None
                and min_remainder != 0
                and part.item_count > min_remainder
            ):
                quantity = part.item_count - min_remainder
            # добавляем срез комплектующих на удаление
            items = unreserved_current.filter(part=part)
            batch_delete += list(items[:quantity])

    if batch_delete:
        for item in batch_delete:
            item.delete()

    return len(batch_delete)


def wrap_in_color(color, string=None, link=False):
    colors = {"red", "yellow", "blue", "green"}
    if color in colors:
        if link:
            attrs = {
                "class": f"{color} item-pill link-dark text-decoration-none"
            }
            return attrs
        return f'<span class="{color} item-pill">{string}</span>'
    return string or ""
