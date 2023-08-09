from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from clients.models import Job

User = get_user_model()


class Order(models.Model):
    current = models.BooleanField("текущий", default=True)
    date = models.DateTimeField("дата", default=timezone.now)
    invoice_number = models.CharField(
        "номер счёта", max_length=100, blank=True, null=True
    )

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"

    def __str__(self) -> str:
        status = "оформлен"
        if self.current:
            status = "текущий"
        return f"Заказ {self.id} ({status})"

    def get_absolute_url(self):
        url = reverse("inventory:order_by_id", kwargs={"pk": self.pk})
        if self.current:
            url = reverse("inventory:order")
        return url


class Manufacturer(models.Model):
    name = models.CharField(
        max_length=1024, unique=True, blank=False, null=False
    )

    class Meta:
        verbose_name = "производитель"
        verbose_name_plural = "производители"

    def __str__(self):
        return f"{self.name}"


class Vendor(models.Model):
    name = models.CharField(
        max_length=1024, unique=True, blank=False, null=False
    )

    class Meta:
        verbose_name = "поставщик"
        verbose_name_plural = "поставщики"

    def __str__(self):
        return f"{self.name}"


class Part(models.Model):
    vendor_code = models.CharField("артикул", max_length=256, unique=True)
    name = models.CharField("наименование", max_length=1024)
    units = models.CharField("единицы", max_length=100, blank=True, null=True)
    price = models.DecimalField(
        "цена, руб.", max_digits=11, decimal_places=2, blank=True, null=True
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name="производитель",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    vendor = models.ForeignKey(
        Vendor,
        verbose_name="поставщик",
        on_delete=models.CASCADE,
        null=True,
        limit_choices_to=~models.Q(name="2"),
    )
    note = models.CharField(
        "примечание", max_length=1024, blank=True, null=True
    )
    minimum_remainder = models.SmallIntegerField(
        "неснижаемый остаток",
        default=0,
    )

    @property
    def quantity_total(self):
        """
        Кол-во комплектующих, которые
        пришли на склад, и не взяты в работу.
        """
        total = self.items.filter(job=None, arrived=True).count()
        return f"{total}"

    quantity_total.fget.short_description = "кол-во"

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields if f.name != "units"]

    class Meta:
        verbose_name = "модель комплектующей"
        verbose_name_plural = "номенклатура"

    def __str__(self) -> str:
        return f"{self.vendor_code} - {self.name}"

    def get_absolute_url(self):
        return reverse("inventory:items", kwargs={"pk": self.pk})


class Item(models.Model):
    """
    Модель комплектующей.
    """

    part = models.ForeignKey(
        Part,
        verbose_name="Артикул",
        on_delete=models.CASCADE,
        related_name="items",
        blank=False,
        null=False,
    )
    date = models.DateField("Дата", default=timezone.now)
    arrived = models.BooleanField("Пришло", default=False)
    vendor2 = models.BooleanField("Поставщик 2", default=False)
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
        verbose_name="заказ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
    )
    price = models.DecimalField(
        "цена, руб.", max_digits=11, decimal_places=2, default=Decimal("0.00")
    )
    free_order = models.BooleanField(
        "Свободный заказ",
        default=False,
        help_text="Запретить удаление из заказа при пересчёте резервов.",
    )

    @property
    def in_warehouse(self):
        if not self.arrived:
            return False
        if self.job is not None:
            return False
        return True

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "комплектующая"
        verbose_name_plural = "комплектующие"

    def __str__(self):
        return str(self.part.vendor_code)

    def get_absolute_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            kwargs={"object_id": self.id},
        )


class InventoryLog(models.Model):
    class Operation(models.TextChoices):
        EMPTY = "", _("---выбрать---")
        RECEPTION = "RECEPTION", _("Приход")
        RETURN = "RETURN", _("Возврат")
        TAKE = "TAKE", _("Расход")

    operation = models.CharField(
        "операция", max_length=32, choices=Operation.choices
    )
    items = models.ManyToManyField(
        Item, verbose_name="комплектующие", related_name="logs"
    )
    job = models.ForeignKey(
        Job,
        verbose_name="клиент",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    date = models.DateTimeField("дата", default=timezone.now)
    comment = models.CharField("комментарий", max_length=1024, blank=True)

    class Meta:
        verbose_name = "операция на складе"
        verbose_name_plural = "операции на складе"

    def __str__(self):
        return f"{self.operation}"

    def get_absolute_url(self):
        return reverse("inventory:log_items", kwargs={"pk": self.pk})


class Prosthesis(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    class ProsthesisType(models.TextChoices):
        T1 = 1, "тип 1"
        T2 = 2, "тип 2"
        T3 = 3, "тип 3"
        T4 = 4, "тип 4"

    number = models.CharField("артикул", max_length=512, unique=True)
    kind = models.CharField(
        "тип", max_length=1024, blank=True, choices=ProsthesisType.choices
    )
    # name = models.CharField("наименование", max_length=1024, blank=True)
    price = models.DecimalField("стоимость", max_digits=11, decimal_places=2)
    region = models.CharField("регион", max_length=128, choices=Region.choices)

    class Meta:
        verbose_name = "протез"
        verbose_name_plural = "протезы"

    def __str__(self) -> str:
        return f"{self.number}"
