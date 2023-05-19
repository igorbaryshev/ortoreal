from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from clients.models import Client, Job

User = get_user_model()


class Order(models.Model):
    current = models.BooleanField("Текущий", default=True)
    date = models.DateTimeField("Дата", default=timezone.now)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self) -> str:
        current = "оформлен"
        if self.current:
            current = "текущий"
        return f"Заказ {self.id} ({current})"

    def get_absolute_url(self):
        url = reverse("inventory:order_by_id", kwargs={"pk": self.pk})
        if self.current:
            url = reverse("inventory:order")
        return url


class Vendor(models.Model):
    name = models.CharField(
        max_length=1024, unique=True, blank=False, null=False
    )

    class Meta:
        verbose_name = "Производитель/поставщик"
        verbose_name_plural = "Производители/поставщики"

    def __str__(self):
        return f"{self.name}"


class Part(models.Model):
    class Units(models.TextChoices):
        PAIRS = "pairs", _("пар")
        PIECES = "pieces", _("шт.")
        SETS = "sets", _("компл.")
        PACKAGES = "packages", _("упак.")
        ITEMS = "items", _("ед.")
        METERS = "meters", _("м.")

    vendor_code = models.CharField("Артикул", max_length=256, unique=True)
    name = models.CharField("Наименование", max_length=1024)
    units = models.CharField(
        "Единицы",
        max_length=32,
        choices=Units.choices,
        blank=True,
        default=Units.ITEMS,
    )
    price = models.DecimalField(
        "Цена, руб.", max_digits=11, decimal_places=2, blank=True, null=True
    )
    vendor = models.ForeignKey(
        Vendor,
        verbose_name="Производитель/поставщик",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    note = models.CharField("Примечание", max_length=1024, blank=True)
    minimum_remainder = models.SmallIntegerField(
        "Неснижаемый остаток",
        blank=True,
        null=True,
        help_text="Оставьте пустым или 0, чтобы выключить неснижаемый остаток.",
    )

    @property
    def quantity_s1(self):
        quantity = self.items.filter(
            warehouse=Item.Warehouse.S1, job=None
        ).count()
        return f"{quantity}"

    quantity_s1.fget.short_description = "Кол-во(С1)"

    @property
    def quantity_s2(self):
        quantity = self.items.filter(
            warehouse=Item.Warehouse.S2, job=None
        ).count()
        return f"{quantity}"

    quantity_s2.fget.short_description = "Кол-во(С2)"

    @property
    def quantity_total(self):
        """
        Кол-во комплектующих, которые
        пришли на склад, и не взяты в работу.
        """
        total = self.items.filter(job=None, warehouse__isnull=False).count()
        return f"{total}"

    quantity_total.fget.short_description = "Кол-во"

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields if f.name != "units"]

    class Meta:
        verbose_name = "модель комплектующей"
        verbose_name_plural = "Номенклатура"

    def __str__(self) -> str:
        return f"{self.vendor_code} - {self.name}"

    def get_absolute_url(self):
        return reverse("admin:inventory_part_change", kwargs={"pk": self.pk})


class Item(models.Model):
    class Warehouse(models.IntegerChoices):
        S1 = 1, _("Склад 1")
        S2 = 2, _("Склад 2")

    part = models.ForeignKey(
        Part,
        verbose_name="Артикул",
        on_delete=models.CASCADE,
        related_name="items",
        blank=False,
        null=False,
    )
    date = models.DateField("Дата", default=timezone.now)
    warehouse = models.PositiveSmallIntegerField(
        "Склад", blank=True, null=True, choices=Warehouse.choices
    )
    job = models.ForeignKey(
        Job,
        verbose_name="Работа",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
    )
    reserved = models.ForeignKey(
        Job,
        verbose_name="Резерв",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reserved_items",
    )
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
    )
    free_order = models.BooleanField(
        "Свободный заказ",
        default=False,
        help_text="Запретить удаление из заказа при пересчёте резервов.",
    )

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "Комплектующая"
        verbose_name_plural = "Комплектующие"

    def __str__(self):
        return self.part.__str__()


class InventoryLog(models.Model):
    class Operation(models.TextChoices):
        EMPTY = "", _("---выбрать---")
        RECEPTION = "RECEPTION", _("Приход")
        RETURN = "RETURN", _("Возврат")
        TAKE = "TAKE", _("Расход")

    operation = models.CharField(
        "Операция", max_length=32, choices=Operation.choices
    )
    items = models.ManyToManyField(
        Item, verbose_name="Комплектующие", related_name="logs"
    )
    job = models.ForeignKey(
        Job,
        verbose_name="Клиент",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    date = models.DateTimeField("Дата", default=timezone.now)
    comment = models.CharField("Комментарий", max_length=1024, blank=True)

    class Meta:
        verbose_name = "Операция на складе"
        verbose_name_plural = "Операции на складе"

    def __str__(self):
        return f"{self.operation}"

    def get_absolute_url(self):
        return reverse("inventory:log_items", kwargs={"pk": self.pk})


class Prosthesis(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    number = models.CharField("Номер изделия", max_length=150, unique=True)
    kind = models.CharField("Вид", max_length=1024, blank=True)
    name = models.CharField("Наименование", max_length=1024, blank=True)
    price = models.DecimalField("Стоимость", max_digits=11, decimal_places=2)
    region = models.CharField("Регион", max_length=128, choices=Region.choices)

    class Meta:
        verbose_name = "Протез"
        verbose_name_plural = "Протезы"

    def __str__(self) -> str:
        return f"{self.number}"
